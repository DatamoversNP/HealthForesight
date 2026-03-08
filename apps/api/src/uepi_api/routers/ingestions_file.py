"""Ingestion routes using file storage (for local development)"""
from typing import Annotated, List, Optional, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel
import tempfile
import os
import json
from pathlib import Path

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_ingestions import (
    list_ingestions,
    get_ingestion,
    create_ingestion,
    update_ingestion,
    delete_ingestion,
)

router = APIRouter()


class IngestionCreate(BaseModel):
    ingestion_type: str
    manifest_uri: str = ""


class IngestionUpdate(BaseModel):
    status: str | None = None
    manifest_uri: str | None = None
    metadata: dict | None = None


@router.get("/ingestions", response_model=List[dict])
async def get_ingestions(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all ingestions for the current tenant, sorted by most recent first"""
    ingestions = list_ingestions(current_user.tenant_id)
    # Sort by created_at descending (most recent first)
    ingestions_sorted = sorted(
        ingestions,
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )
    # Apply pagination
    return ingestions_sorted[skip:skip + limit]


@router.get("/ingestions/last-executed", response_model=dict)
async def get_last_executed_ingestion(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get the last executed ingestion for the current tenant"""
    ingestions = list_ingestions(current_user.tenant_id)
    
    # Also check pipeline runs as fallback
    if not ingestions:
        from uepi_api.storage_pipelines import list_pipelines
        from uepi_api.storage_pipeline_runs import list_pipeline_runs
        
        # Get all pipelines and their runs
        pipelines = list_pipelines(current_user.tenant_id)
        all_runs = []
        for pipeline in pipelines:
            try:
                pipeline_id = pipeline.get("pipeline_id")
                if isinstance(pipeline_id, str):
                    pipeline_id = UUID(pipeline_id)
                # Note: list_pipeline_runs takes tenant_id first, then pipeline_id
                runs = list_pipeline_runs(current_user.tenant_id, pipeline_id)
                # Add pipeline info to each run for matching
                for run in runs:
                    run["_pipeline_id"] = str(pipeline_id)
                    run["_pipeline"] = pipeline
                all_runs.extend(runs)
            except Exception as e:
                print(f"Error loading runs for pipeline {pipeline.get('pipeline_id')}: {e}")
                continue
        
        # Find the most recent completed run
        completed_runs = [r for r in all_runs if r.get("status") == "COMPLETED"]
        if completed_runs:
            latest_run = max(completed_runs, key=lambda x: x.get("completed_at", "") or "")
            # Convert pipeline run to ingestion-like format
            pipeline = latest_run.get("_pipeline", {})
            return {
                "id": latest_run.get("run_id"),
                "tenant_id": str(current_user.tenant_id),
                "ingestion_type": pipeline.get("target_dataset_type", "UNKNOWN") if pipeline else "UNKNOWN",
                "status": "COMPLETED",
                "manifest_uri": latest_run.get("output_uri", ""),
                "started_at": latest_run.get("started_at"),
                "completed_at": latest_run.get("completed_at"),
                "metadata": {
                    "pipeline_id": latest_run.get("pipeline_id"),
                    "pipeline_name": pipeline.get("pipeline_name", "") if pipeline else "",
                    "run_id": latest_run.get("run_id"),
                    **latest_run.get("metadata", {}),
                },
                "created_at": latest_run.get("started_at", ""),
            }
    
    if not ingestions:
        raise HTTPException(status_code=404, detail="No ingestions found")
    
    # Sort by completed_at descending, filter to completed ones
    completed = [ing for ing in ingestions if ing.get("status") == "COMPLETED"]
    if not completed:
        # If no completed, return most recent
        ingestions_sorted = sorted(
            ingestions,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        return ingestions_sorted[0] if ingestions_sorted else {}
    
    completed_sorted = sorted(
        completed,
        key=lambda x: x.get("completed_at", ""),
        reverse=True
    )
    return completed_sorted[0]


@router.get("/ingestions/{ingestion_id}", response_model=dict)
async def get_ingestion_by_id(
    ingestion_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get an ingestion by ID"""
    ingestion = get_ingestion(ingestion_id, current_user.tenant_id)
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    return ingestion


@router.post("/ingestions", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_ingestion_route(
    ingestion_data: IngestionCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new ingestion"""
    ingestion = create_ingestion(
        current_user.tenant_id,
        {
            "ingestion_type": ingestion_data.ingestion_type,
            "manifest_uri": ingestion_data.manifest_uri,
            "status": "PENDING",
        }
    )
    return ingestion


@router.put("/ingestions/{ingestion_id}", response_model=dict)
async def update_ingestion_route(
    ingestion_id: UUID,
    ingestion_data: IngestionUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update an ingestion"""
    ingestion = update_ingestion(ingestion_id, current_user.tenant_id, ingestion_data.model_dump(exclude_unset=True))
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    return ingestion


@router.post("/ingestions/{ingestion_id}/run", response_model=dict)
async def run_ingestion_route(
    ingestion_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Manually trigger/rerun an ingestion"""
    ingestion = get_ingestion(ingestion_id, current_user.tenant_id)
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    
    from datetime import datetime, timezone
    
    # Update status to PROCESSING
    updated = update_ingestion(
        ingestion_id,
        current_user.tenant_id,
        {
            "status": "PROCESSING",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    
    # In a real implementation, this would trigger the worker
    # For now, simulate immediate completion
    updated = update_ingestion(
        ingestion_id,
        current_user.tenant_id,
        {
            "status": "COMPLETED",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    
    return updated


@router.delete("/ingestions/{ingestion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingestion_route(
    ingestion_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Delete an ingestion"""
    success = delete_ingestion(ingestion_id, current_user.tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ingestion not found")


class SchemaAnalysisResponse(BaseModel):
    format: str
    columns: List[Dict[str, Any]]
    canonical_schema: Dict[str, Any]
    mapping_suggestions: Dict[str, str]
    coverage: Dict[str, Any]


@router.post("/ingestions/analyze-schema", response_model=SchemaAnalysisResponse)
async def analyze_schema_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    file: UploadFile = File(...),
    ingestion_type: str = Form(...),
):
    """Analyze uploaded file schema and suggest mappings to comprehensive canonical schema"""
    from uepi_common.ingestion.comprehensive_processor import ComprehensiveIngestionProcessor

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        processor = ComprehensiveIngestionProcessor(
            tenant_id=current_user.tenant_id,
            dataset_type=ingestion_type,
            source_system="FILE_UPLOAD",
        )
        analysis_result = processor.analyze_schema(tmp_path)
        return SchemaAnalysisResponse(**analysis_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema analysis failed: {str(e)}")
    finally:
        os.unlink(tmp_path)


class IngestionProcessingResult(BaseModel):
    success: bool
    ingestion_id: UUID
    raw_zone_uri: Optional[str] = None
    curated_partitions: List[str] = []  # Default to empty list if not provided
    record_count: int
    records_valid: int
    records_invalid: int
    errors: List[Dict[str, Any]] = []  # Default to empty list
    warnings: List[Dict[str, Any]] = []  # Default to empty list


@router.post("/ingestions/upload", response_model=IngestionProcessingResult, status_code=201)
async def upload_and_ingest_flexible(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    file: UploadFile = File(...),
    ingestion_type: str = Form(...),
    auto_detect_schema: bool = Form(True),
    mapping_config_json: Optional[str] = Form(None),
):
    """Upload file and process ingestion with comprehensive canonical schema handling"""
    from uepi_common.ingestion.comprehensive_processor import ComprehensiveIngestionProcessor
    from datetime import datetime, timezone
    from uuid import uuid4
    import json

    mapping_config = json.loads(mapping_config_json) if mapping_config_json else None

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    ingestion_id = uuid4()
    initial_ingestion_record = create_ingestion(
        current_user.tenant_id,
        {
            "id": str(ingestion_id),
            "ingestion_type": ingestion_type,
            "manifest_uri": f"local://{file.filename}",
            "status": "PROCESSING",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    try:
        processor = ComprehensiveIngestionProcessor(
            tenant_id=current_user.tenant_id,
            dataset_type=ingestion_type,
            source_system="FILE_UPLOAD",
            ingestion_id=ingestion_id,
        )
        print(f"Processing file: {tmp_path}")
        print(f"  auto_detect_schema: {auto_detect_schema}")
        print(f"  mapping_config: {mapping_config is not None}")
        
        processing_result = processor.process_file(
            file_path=tmp_path,
            auto_detect_schema=auto_detect_schema,
            mapping_config=mapping_config,
        )
        print(f"✅ Processing complete: success={processing_result.get('success')}")

        status_str = "COMPLETED" if processing_result["success"] else "FAILED"
        ingestion_metadata = {
            "processing_summary": {
                "record_count": processing_result["record_count"],
                "records_valid": processing_result["records_valid"],
                "records_invalid": processing_result["records_invalid"],
                "errors": processing_result["errors"],
                "warnings": processing_result["warnings"],
            },
            "coverage": processing_result.get("coverage", {}),
            "raw_zone_uri": processing_result.get("raw_zone_uri"),
            "curated_zone_uri": processing_result.get("curated_zone_uri"),
            "curated_partitions": processing_result.get("curated_partitions", []),
        }
        
        updated_ingestion = update_ingestion(
            ingestion_id,
            current_user.tenant_id,
            {
                "status": status_str,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "metadata": ingestion_metadata,
            }
        )
        
        # Integration: Create data period when ingestion completes successfully
        if status_str == "COMPLETED":
            try:
                from uepi_api.integration_helpers import create_data_period_from_ingestion
                period = create_data_period_from_ingestion(
                    tenant_id=current_user.tenant_id,
                    ingestion_id=str(ingestion_id),
                    ingestion_metadata=ingestion_metadata,
                )
                if period:
                    print(f"Created data period {period.get('period_id')} for ingestion {ingestion_id}")
            except Exception as e:
                # Don't fail ingestion if data period creation fails
                print(f"Warning: Failed to create data period for ingestion {ingestion_id}: {e}")

        # Ensure all required fields are present
        result_data = {
            "ingestion_id": ingestion_id,
            "success": processing_result.get("success", False),
            "record_count": processing_result.get("record_count", 0),
            "records_valid": processing_result.get("records_valid", 0),
            "records_invalid": processing_result.get("records_invalid", 0),
            "raw_zone_uri": processing_result.get("raw_zone_uri"),
            "curated_partitions": processing_result.get("curated_partitions", []),
            "errors": processing_result.get("errors", []),
            "warnings": processing_result.get("warnings", []),
        }
        
        return IngestionProcessingResult(**result_data)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_message = f"{str(e)}\n\nTraceback:\n{error_traceback}"
        
        print(f"ERROR: Ingestion failed for {ingestion_id}:")
        print(error_message)
        
        update_ingestion(
            ingestion_id,
            current_user.tenant_id,
            {
                "status": "FAILED",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {"error": str(e), "traceback": error_traceback},
            }
        )
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.get("/ingestions/{ingestion_id}/view-source")
async def view_source_data(
    ingestion_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """View source data from ingestion (raw data before processing)"""
    ingestion = get_ingestion(ingestion_id, current_user.tenant_id)
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    
    # Read from raw zone if available
    manifest_uri = ingestion.get("manifest_uri", "")
    
    # Try to read from local file
    import pandas as pd
    from pathlib import Path
    
    file_path = None
    if manifest_uri.startswith("local://"):
        file_name = manifest_uri.replace("local://", "")
        # Look for file in data directory
        data_dir = Path("data/source_data/raw") / str(current_user.tenant_id)
        file_path = data_dir / file_name
        if not file_path.exists():
            # Try in uploads directory
            file_path = Path("data/uploads") / file_name
    
    if file_path and file_path.exists():
        try:
            # Read file based on extension
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path, nrows=limit + offset)
            elif file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path, nrows=limit + offset)
            
            # Apply pagination
            df_paginated = df.iloc[offset:offset + limit]
            
            return {
                "ingestion_id": str(ingestion_id),
                "raw_uri": str(file_path),
                "rows": df_paginated.to_dict("records"),
                "total_count": len(df),
                "limit": limit,
                "offset": offset,
                "columns": list(df.columns),
            }
        except Exception as e:
            return {
                "ingestion_id": str(ingestion_id),
                "raw_uri": str(file_path),
                "rows": [],
                "total_count": 0,
                "error": str(e),
            }
    
    return {
        "ingestion_id": str(ingestion_id),
        "raw_uri": manifest_uri,
        "rows": [],
        "total_count": 0,
        "limit": limit,
        "offset": offset,
        "message": "Source data file not found. It may have been processed and moved.",
    }


@router.get("/ingestions/{ingestion_id}/view-curated")
async def view_curated_data(
    ingestion_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """View curated data from ingestion (processed data in canonical format)"""
    ingestion = get_ingestion(ingestion_id, current_user.tenant_id)
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    
    # Read from curated zone
    curated_uri = ingestion.get("metadata", {}).get("curated_zone_uri", "")
    
    import pandas as pd
    from pathlib import Path
    
    if curated_uri.startswith("local_target://") or curated_uri.startswith("local_curated://"):
        # Parse URI: local_target://tenant_id/dataset_type/YYYY/MM/data.parquet
        # Also support legacy local_curated:// for backward compatibility
        uri_prefix = "local_target://" if curated_uri.startswith("local_target://") else "local_curated://"
        parts = curated_uri.replace(uri_prefix, "").split("/")
        if len(parts) >= 3:
            dataset_type = parts[1]
            file_path = Path("data/target_data_model") / "/".join(parts[0:])
            
            # Find most recent file for this ingestion
            if file_path.parent.exists():
                files = sorted(file_path.parent.glob("*.parquet"), reverse=True)
                if files:
                    file_path = files[0]
            
            if file_path.exists():
                try:
                    df = pd.read_parquet(file_path)
                    df_paginated = df.iloc[offset:offset + limit]
                    
                    return {
                        "ingestion_id": str(ingestion_id),
                        "curated_uri": curated_uri,
                        "rows": df_paginated.to_dict("records"),
                        "total_count": len(df),
                        "limit": limit,
                        "offset": offset,
                        "columns": list(df.columns),
                        "coverage": ingestion.get("metadata", {}).get("coverage", {}),
                    }
                except Exception as e:
                    return {
                        "ingestion_id": str(ingestion_id),
                        "curated_uri": curated_uri,
                        "rows": [],
                        "error": str(e),
                    }
    
    return {
        "ingestion_id": str(ingestion_id),
        "curated_uri": curated_uri,
        "rows": [],
        "total_count": 0,
        "limit": limit,
        "offset": offset,
        "message": "Curated data not available yet.",
    }

