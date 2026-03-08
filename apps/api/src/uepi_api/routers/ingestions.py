"""Ingestion endpoints"""
from typing import Annotated
from uuid import UUID
import tempfile
import os
import json

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, InterfaceError, InvalidRequestError
try:
    import boto3
except (ImportError, PermissionError):
    boto3 = None  # Optional - only needed for S3 storage
import sqlalchemy.exc

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.database import get_db
from uepi_api.models.ingestion import Ingestion, IngestionError, IngestionStatus, IngestionType
from uepi_api.config import get_settings

router = APIRouter()


class IngestionCreate(BaseModel):
    """Ingestion creation model"""
    ingestion_type: IngestionType
    manifest_uri: str


class IngestionResponse(BaseModel):
    """Ingestion response model"""
    id: UUID
    tenant_id: UUID
    ingestion_type: str
    status: str
    manifest_uri: str
    started_at: str | None
    completed_at: str | None
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/ingestions", response_model=list[IngestionResponse])
async def list_ingestions(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all ingestions for the current tenant"""
    try:
        ingestions = db.query(Ingestion).filter(
            Ingestion.tenant_id == current_user.tenant_id,
        ).order_by(Ingestion.created_at.desc()).offset(skip).limit(limit).all()
        return ingestions
    except Exception as e:
        # If database query fails, return empty list (database not available)
        print(f"Database query failed in list_ingestions: {e}")
        import traceback
        traceback.print_exc()
        return []


@router.post("/ingestions", response_model=IngestionResponse, status_code=201)
async def create_ingestion(
    ingestion_data: IngestionCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create a new ingestion job"""
    ingestion = Ingestion(
        tenant_id=current_user.tenant_id,
        ingestion_type=ingestion_data.ingestion_type.value,
        status=IngestionStatus.PENDING.value,
        manifest_uri=ingestion_data.manifest_uri,
    )
    db.add(ingestion)
    db.commit()
    db.refresh(ingestion)
    
    # Trigger worker job
    try:
        from uepi_worker.tasks import ingest_claims_job
        ingest_claims_job.delay(
            str(current_user.tenant_id),
            ingestion_data.manifest_uri,
            str(ingestion.id),
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to trigger ingestion job: {e}")
    
    return ingestion


@router.post("/ingestions/upload", response_model=IngestionResponse, status_code=201)
async def upload_and_ingest(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    file: UploadFile = File(...),
    ingestion_type: str = Form(...),
    replace_existing: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Upload file and process ingestion (Phase 3: Manual Upload)
    
    This endpoint:
    1. Validates file format
    2. Saves file to temp location
    3. Validates schema using data contracts
    4. Writes to raw zone (immutable original)
    5. Transforms and writes to curated zone (partitioned Parquet)
    6. Creates ingestion record and triggers worker job
    """
    settings = get_settings()
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    file_format_map = {'.csv': 'csv', '.parquet': 'parquet', '.json': 'json'}
    if file_ext not in file_format_map:
        raise HTTPException(status_code=400, detail="File must be CSV, Parquet, or JSON")
    
    file_format = file_format_map[file_ext]
    
    # Validate ingestion type and map to DatasetType
    try:
        ingestion_type_enum = IngestionType(ingestion_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid ingestion type: {ingestion_type}")
    
    # Map IngestionType to DatasetType
    from uepi_common.data_contracts.manifest import DatasetType
    dataset_type_map = {
        IngestionType.CLAIMS: DatasetType.CLAIMS_LINES,
        IngestionType.ENROLLMENT: DatasetType.ENROLLMENT,
        IngestionType.PROVIDERS: DatasetType.PROVIDERS,
        IngestionType.BENEFIT_DESIGN: DatasetType.BENEFIT_DESIGN,
    }
    dataset_type = dataset_type_map.get(ingestion_type_enum, DatasetType.CLAIMS_LINES)
    
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Process file using ingestion processor
        from uepi_common.data.parquet_service import ParquetDataService
        from uepi_common.ingestion.processor import IngestionProcessor
        from uepi_common.data_contracts.manifest import IngestionMode
        
        parquet_service = ParquetDataService(container=settings.object_storage.bucket_name_or_bucket)
        processor = IngestionProcessor(
            tenant_id=current_user.tenant_id,
            dataset_type=dataset_type,
            parquet_service=parquet_service,
        )
        
        # Process file: validate → raw zone → curated zone
        result = processor.process_file(
            file_path=tmp_path,
            file_format=file_format,
            ingestion_mode=IngestionMode.MANUAL_UPLOAD,
            replace_existing=replace_existing,
        )
        
        if not result["success"]:
            # Validation failed - create ingestion record with errors
            ingestion = Ingestion(
                tenant_id=current_user.tenant_id,
                ingestion_type=ingestion_type_enum.value,
                status=IngestionStatus.FAILED.value,
                manifest_uri=f"local://{tmp_path}",  # Temporary manifest
            )
            db.add(ingestion)
            
            # Store validation errors
            for error in result.get("errors", []):
                from uepi_api.models.ingestion import IngestionError
                ingestion_error = IngestionError(
                    tenant_id=current_user.tenant_id,
                    ingestion_id=ingestion.id,
                    error_type="VALIDATION",
                    error_message=str(error),
                    row_number=error.get("row", None),
                    file_path=file.filename,
                )
                db.add(ingestion_error)
            
            db.commit()
            db.refresh(ingestion)
            
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "File validation failed",
                    "validation_result": result.get("validation_result", {}),
                    "errors": result.get("errors", []),
                }
            )
        
        # Create manifest URI
        from datetime import datetime
        manifest_uri = result.get("raw_zone_uri", f"s3://{settings.object_storage.bucket_name_or_bucket}/raw/{file.filename}")
        
        # Create ingestion record
        ingestion = Ingestion(
            tenant_id=current_user.tenant_id,
            ingestion_type=ingestion_type_enum.value,
            status=IngestionStatus.COMPLETED.value,  # Already processed synchronously
            manifest_uri=manifest_uri,
        )
        db.add(ingestion)
        db.commit()
        db.refresh(ingestion)
        
        # Store warnings if any
        for warning in result.get("warnings", []):
            from uepi_api.models.ingestion import IngestionError
            ingestion_error = IngestionError(
                tenant_id=current_user.tenant_id,
                ingestion_id=ingestion.id,
                error_type="WARNING",
                error_message=str(warning.get("message", warning)),
                file_path=file.filename,
            )
            db.add(ingestion_error)
        db.commit()
        
        # Create dataset snapshot records for curated partitions
        for partition_uri in result.get("curated_partitions", []):
            # Extract partition info from URI
            # Format: {tenant_id}/curated/{dataset_type}/year={year}/month={month}/lob={lob}/market={market}/data.parquet
            parts = partition_uri.split("/")
            partition_values = {}
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    partition_values[key] = value
            
            # Create or update dataset snapshot
            from uepi_api.models.ingestion import Dataset
            existing_dataset = db.query(Dataset).filter(
                Dataset.tenant_id == current_user.tenant_id,
                Dataset.dataset_type == dataset_type.value,
                Dataset.year == int(partition_values.get("year", 0)),
                Dataset.month == int(partition_values.get("month", 0)),
                Dataset.lob == partition_values.get("lob"),
                Dataset.market == partition_values.get("market"),
            ).first()
            
            if existing_dataset:
                # Update existing snapshot
                existing_dataset.record_count = result.get("record_count", 0)
                existing_dataset.data_uri = partition_uri
                existing_dataset.updated_at = datetime.utcnow()
            else:
                # Create new snapshot
                dataset = Dataset(
                    tenant_id=current_user.tenant_id,
                    dataset_type=dataset_type.value,
                    year=int(partition_values.get("year", 0)),
                    month=int(partition_values.get("month", 0)),
                    lob=partition_values.get("lob"),
                    market=partition_values.get("market"),
                    record_count=result.get("record_count", 0),
                    data_uri=partition_uri,
                )
                db.add(dataset)
        db.commit()
        
        return ingestion
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/ingestions/{ingestion_id}", response_model=IngestionResponse)
async def get_ingestion(
    ingestion_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get ingestion by ID"""
    ingestion = db.query(Ingestion).filter(
        Ingestion.id == ingestion_id,
        Ingestion.tenant_id == current_user.tenant_id,
    ).first()
    
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    
    return ingestion


@router.get("/ingestions/{ingestion_id}/errors")
async def get_ingestion_errors(
    ingestion_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get errors for an ingestion"""
    ingestion = db.query(Ingestion).filter(
        Ingestion.id == ingestion_id,
        Ingestion.tenant_id == current_user.tenant_id,
    ).first()
    
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    
    errors = db.query(IngestionError).filter(
        IngestionError.ingestion_id == ingestion_id,
        IngestionError.tenant_id == current_user.tenant_id,
    ).all()
    
    return [
        {
            "id": e.id,
            "error_type": e.error_type,
            "error_message": e.error_message,
            "row_number": e.row_number,
            "file_path": e.file_path,
            "created_at": e.created_at.isoformat(),
        }
        for e in errors
    ]


@router.get("/datasets")
async def list_datasets(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    dataset_type: str | None = Query(None),
    year: int | None = Query(None),
    month: int | None = Query(None),
    lob: str | None = Query(None),
    market: str | None = Query(None),
):
    """List available datasets"""
    try:
        from uepi_api.models.ingestion import Dataset
        
        query = db.query(Dataset).filter(Dataset.tenant_id == current_user.tenant_id)
        
        if dataset_type:
            query = query.filter(Dataset.dataset_type == dataset_type)
        if year:
            query = query.filter(Dataset.year == year)
        if month:
            query = query.filter(Dataset.month == month)
        if lob:
            query = query.filter(Dataset.lob == lob)
        if market:
            query = query.filter(Dataset.market == market)
        
        datasets = query.order_by(Dataset.year.desc(), Dataset.month.desc()).all()
        
        return [
            {
                "id": str(d.id),
                "dataset_type": d.dataset_type,
                "year": d.year,
                "month": d.month,
                "lob": d.lob,
                "market": d.market,
                "record_count": d.record_count,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in datasets
        ]
    except (OperationalError, InterfaceError, InvalidRequestError) as e:
        # Handle database/model initialization errors gracefully
        import traceback
        print(f"Database/model error in list_datasets: {e}")
        traceback.print_exc()
        # Return empty list instead of crashing
        return []
    except Exception as e:
        # Handle any other errors
        import traceback
        print(f"Unexpected error in list_datasets: {e}")
        traceback.print_exc()
        return []


class ScheduledIngestionCreate(BaseModel):
    """Scheduled ingestion creation model"""
    ingestion_type: IngestionType
    source_type: str  # 'SFTP', 'BLOB_DROP', 'API_PULL'
    source_config: dict  # Source-specific configuration (SFTP credentials, blob path, API endpoint)
    schedule_cron: str  # Cron expression (e.g., '0 2 * * *' for daily at 2 AM)
    incremental: bool = True  # Incremental ingestion (only new months)
    notification_email: str | None = None  # Email for failure notifications


@router.post("/ingestions/scheduled", response_model=IngestionResponse, status_code=201)
async def create_scheduled_ingestion(
    ingestion_data: ScheduledIngestionCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create scheduled ingestion job (Phase 3: Scheduled Ingestion)
    
    This endpoint creates a scheduled ingestion configuration that will:
    1. Run on a cron schedule (e.g., daily, weekly, monthly)
    2. Pull data from configured source (SFTP/blob drop/API)
    3. Validate and process using IngestionProcessor
    4. Send notifications on failure
    
    Note: For MVP, this creates the configuration. Actual scheduling is done via:
    - Celery Beat (for development/staging)
    - Kubernetes CronJob (for production)
    """
    # Create ingestion record with schedule metadata
    ingestion = Ingestion(
        tenant_id=current_user.tenant_id,
        ingestion_type=ingestion_data.ingestion_type.value,
        status=IngestionStatus.PENDING.value,
        manifest_uri=f"scheduled://{ingestion_data.source_type}",  # Placeholder manifest URI
        metadata_json={
            "source_type": ingestion_data.source_type,
            "source_config": ingestion_data.source_config,
            "schedule_cron": ingestion_data.schedule_cron,
            "incremental": ingestion_data.incremental,
            "notification_email": ingestion_data.notification_email,
        },
    )
    db.add(ingestion)
    db.commit()
    db.refresh(ingestion)
    
    # Item 11: Register scheduled job with schedule executor service
    # For file storage, schedules are managed via schedule_executor_service
    # The schedule executor service checks for due schedules periodically
    try:
        from uepi_api.storage_schedules import create_schedule
        from datetime import datetime, timedelta
        
        # Create a schedule for this ingestion if it's recurring
        if ingestion_data.incremental:
            # Schedule daily ingestion
            schedule_data = {
                "schedule_type": "INGESTION",
                "schedule_name": f"Daily {ingestion_data.ingestion_type} Ingestion",
                "cron_expression": "0 2 * * *",  # Daily at 2 AM
                "target_id": str(ingestion.id),
                "enabled": True,
            }
            create_schedule(current_user.tenant_id, schedule_data)
            print(f"✅ Created schedule for ingestion {ingestion.id}")
    except Exception as e:
        # Don't fail ingestion creation if schedule creation fails
        print(f"Warning: Could not create schedule for ingestion: {e}")
    
    return ingestion


class BackfillIngestionCreate(BaseModel):
    """Backfill ingestion creation model"""
    ingestion_type: IngestionType
    manifest_uri: str
    start_date: str  # ISO date string (YYYY-MM-DD)
    end_date: str  # ISO date string (YYYY-MM-DD)
    chunk_size_months: int = 3  # Process in chunks of N months
    throttle_seconds: int = 60  # Delay between chunks


@router.post("/ingestions/backfill", response_model=IngestionResponse, status_code=201)
async def create_backfill_ingestion(
    ingestion_data: BackfillIngestionCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create backfill ingestion job (Phase 3: Backfill Ingestion)
    
    This endpoint creates a backfill job that will:
    1. Process historical data in chunks (to avoid overwhelming the system)
    2. Throttle between chunks (configurable delay)
    3. Resume from last successful chunk if interrupted
    4. Create dataset snapshots for each chunk
    
    For MVP, this creates the job and triggers it. Actual chunking is handled by the worker.
    """
    from datetime import datetime
    
    # Parse dates
    start_date = datetime.fromisoformat(ingestion_data.start_date)
    end_date = datetime.fromisoformat(ingestion_data.end_date)
    
    # Create ingestion record with backfill metadata
    ingestion = Ingestion(
        tenant_id=current_user.tenant_id,
        ingestion_type=ingestion_data.ingestion_type.value,
        status=IngestionStatus.PENDING.value,
        manifest_uri=ingestion_data.manifest_uri,
        metadata_json={
            "backfill": True,
            "start_date": ingestion_data.start_date,
            "end_date": ingestion_data.end_date,
            "chunk_size_months": ingestion_data.chunk_size_months,
            "throttle_seconds": ingestion_data.throttle_seconds,
            "resume_from": None,  # Will be updated if job is interrupted
        },
    )
    db.add(ingestion)
    db.commit()
    db.refresh(ingestion)
    
    # Trigger worker job for backfill processing
    try:
        from uepi_worker.tasks import ingest_job
        ingest_job.delay(
            str(current_user.tenant_id),
            ingestion_data.manifest_uri,
            str(ingestion.id),
            ingestion_data.ingestion_type.value,
        )
        ingestion.status = IngestionStatus.PROCESSING.value
        ingestion.started_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        ingestion.status = IngestionStatus.FAILED.value
        ingestion.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger backfill job: {str(e)}",
        )
    
    return ingestion

