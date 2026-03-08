"""Data Health endpoints - completeness, validation, lineage"""
from typing import Annotated
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import OperationalError, InterfaceError

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.database import get_db
from uepi_api.models.ingestion import Dataset, Ingestion, IngestionError, IngestionStatus
from uepi_api.config import get_settings

router = APIRouter()


@router.get("/data-health/completeness")
async def get_data_completeness(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    dataset_type: str | None = Query(None),
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
):
    """Get data completeness dashboard (months covered by LOB/market)
    
    Returns grid showing:
    - Months covered for each LOB/market combination
    - Missing months (gaps)
    - Record counts
    """
    try:
        query = db.query(Dataset).filter(Dataset.tenant_id == current_user.tenant_id)
        
        if dataset_type:
            query = query.filter(Dataset.dataset_type == dataset_type)
        if start_year:
            query = query.filter(Dataset.year >= start_year)
        if end_year:
            query = query.filter(Dataset.year <= end_year)
        
        datasets = query.all()
        
        # Build completeness grid
        grid: dict[str, dict[str, dict[str, int]]] = {}  # {lob: {market: {month: count}}}
        
        for dataset in datasets:
            lob = dataset.lob or "ALL"
            market = dataset.market or "ALL"
            month_key = f"{dataset.year}-{dataset.month:02d}"
            
            if lob not in grid:
                grid[lob] = {}
            if market not in grid[lob]:
                grid[lob][market] = {}
            
            grid[lob][market][month_key] = dataset.record_count or 0
        
        # Calculate summary statistics
        total_records = sum(d.record_count or 0 for d in datasets)
        unique_months = len(set(f"{d.year}-{d.month:02d}" for d in datasets))
        unique_lobs = len(set(d.lob for d in datasets if d.lob))
        unique_markets = len(set(d.market for d in datasets if d.market))
        
        return {
            "completeness_grid": grid,
            "summary": {
                "total_records": total_records,
                "unique_months": unique_months,
                "unique_lobs": unique_lobs,
                "unique_markets": unique_markets,
                "total_datasets": len(datasets),
            },
            "last_updated": max((d.updated_at for d in datasets), default=None).isoformat() if datasets else None,
        }
        
    except (OperationalError, InterfaceError) as e:
        return {
            "completeness_grid": {},
            "summary": {
                "total_records": 0,
                "unique_months": 0,
                "unique_lobs": 0,
                "unique_markets": 0,
                "total_datasets": 0,
            },
            "last_updated": None,
            "error": "Database unavailable",
        }


@router.get("/data-health/validation-errors")
async def get_validation_errors(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    ingestion_id: UUID | None = Query(None),
    error_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get validation errors with drill-down capability
    
    Returns:
    - Summary by error type
    - Detailed errors with row numbers
    - File paths
    """
    try:
        query = db.query(IngestionError).filter(
            IngestionError.tenant_id == current_user.tenant_id,
        )
        
        if ingestion_id:
            query = query.filter(IngestionError.ingestion_id == ingestion_id)
        if error_type:
            query = query.filter(IngestionError.error_type == error_type)
        
        errors = query.order_by(IngestionError.created_at.desc()).limit(limit).all()
        
        # Group by error type
        error_summary: dict[str, int] = {}
        for error in errors:
            error_summary[error.error_type] = error_summary.get(error.error_type, 0) + 1
        
        return {
            "errors": [
                {
                    "id": str(e.id),
                    "ingestion_id": str(e.ingestion_id),
                    "error_type": e.error_type,
                    "error_message": e.error_message,
                    "row_number": e.row_number,
                    "file_path": e.file_path,
                    "created_at": e.created_at.isoformat(),
                }
                for e in errors
            ],
            "summary": {
                "total_errors": len(errors),
                "by_type": error_summary,
            },
        }
        
    except (OperationalError, InterfaceError) as e:
        return {
            "errors": [],
            "summary": {
                "total_errors": 0,
                "by_type": {},
            },
            "error": "Database unavailable",
        }


@router.get("/data-health/lineage")
async def get_data_lineage(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    dataset_id: UUID | None = Query(None),
    ingestion_id: UUID | None = Query(None),
):
    """Get data lineage (ingestion → dataset → analysis runs)
    
    Returns:
    - Ingestion run history
    - Dataset snapshots
    - Analysis runs using this data
    """
    try:
        lineage = {
            "ingestions": [],
            "datasets": [],
            "analysis_runs": [],
        }
        
        # Get ingestions
        ingestion_query = db.query(Ingestion).filter(Ingestion.tenant_id == current_user.tenant_id)
        if ingestion_id:
            ingestion_query = ingestion_query.filter(Ingestion.id == ingestion_id)
        
        ingestions = ingestion_query.order_by(Ingestion.created_at.desc()).limit(50).all()
        
        lineage["ingestions"] = [
            {
                "id": str(i.id),
                "ingestion_type": i.ingestion_type,
                "status": i.status,
                "manifest_uri": i.manifest_uri,
                "created_at": i.created_at.isoformat(),
                "started_at": i.started_at.isoformat() if i.started_at else None,
                "completed_at": i.completed_at.isoformat() if i.completed_at else None,
            }
            for i in ingestions
        ]
        
        # Get datasets
        dataset_query = db.query(Dataset).filter(Dataset.tenant_id == current_user.tenant_id)
        if dataset_id:
            dataset_query = dataset_query.filter(Dataset.id == dataset_id)
        
        datasets = dataset_query.order_by(Dataset.created_at.desc()).limit(100).all()
        
        lineage["datasets"] = [
            {
                "id": str(d.id),
                "dataset_type": d.dataset_type,
                "year": d.year,
                "month": d.month,
                "lob": d.lob,
                "market": d.market,
                "record_count": d.record_count,
                "data_uri": d.data_uri,
                "created_at": d.created_at.isoformat(),
            }
            for d in datasets
        ]
        
        # Item 12: Add analysis runs linking (Phase 5)
        try:
            from uepi_api.storage_analyses import list_analyses
            from uepi_api.storage_lineage import get_full_lineage
            
            # Get analysis runs for lineage
            all_analyses = list_analyses(current_user.tenant_id)
            analysis_runs = []
            for analysis in all_analyses[:10]:  # Limit to recent 10
                analysis_runs.append({
                    "analysis_id": analysis.get("id"),
                    "analysis_type": analysis.get("analysis_type"),
                    "status": analysis.get("status"),
                    "created_at": analysis.get("created_at"),
                })
            lineage["analysis_runs"] = analysis_runs
        except Exception as e:
            print(f"Warning: Could not load analysis runs for lineage: {e}")
        
        return lineage
        
    except (OperationalError, InterfaceError) as e:
        return {
            "ingestions": [],
            "datasets": [],
            "analysis_runs": [],
            "error": "Database unavailable",
        }


@router.get("/data-health/refresh-status")
async def get_refresh_status(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get refresh timestamps and ingestion run history"""
    try:
        # Get most recent ingestion
        latest_ingestion = db.query(Ingestion).filter(
            Ingestion.tenant_id == current_user.tenant_id,
            Ingestion.status == IngestionStatus.COMPLETED.value,
        ).order_by(Ingestion.completed_at.desc()).first()
        
        # Get ingestion run history (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_ingestions = db.query(Ingestion).filter(
            Ingestion.tenant_id == current_user.tenant_id,
            Ingestion.created_at >= thirty_days_ago,
        ).order_by(Ingestion.created_at.desc()).all()
        
        # Calculate success rate
        total_runs = len(recent_ingestions)
        successful_runs = len([i for i in recent_ingestions if i.status == IngestionStatus.COMPLETED.value])
        failed_runs = len([i for i in recent_ingestions if i.status == IngestionStatus.FAILED.value])
        
        return {
            "last_refresh": latest_ingestion.completed_at.isoformat() if latest_ingestion and latest_ingestion.completed_at else None,
            "last_refresh_status": latest_ingestion.status if latest_ingestion else None,
            "recent_runs": [
                {
                    "id": str(i.id),
                    "ingestion_type": i.ingestion_type,
                    "status": i.status,
                    "created_at": i.created_at.isoformat(),
                    "completed_at": i.completed_at.isoformat() if i.completed_at else None,
                }
                for i in recent_ingestions
            ],
            "statistics": {
                "total_runs_30d": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            },
        }
        
    except (OperationalError, InterfaceError) as e:
        return {
            "last_refresh": None,
            "last_refresh_status": None,
            "recent_runs": [],
            "statistics": {
                "total_runs_30d": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "success_rate": 0,
            },
            "error": "Database unavailable",
        }

