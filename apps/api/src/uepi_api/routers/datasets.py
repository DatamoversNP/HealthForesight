"""Dataset viewing endpoints - for data viewer with filtering"""
from typing import Annotated, Optional
from uuid import UUID
import tempfile
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
import boto3
import polars as pl

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.database import get_db
from uepi_api.models.ingestion import Dataset
from uepi_api.config import get_settings

router = APIRouter()


class DatasetViewRequest(BaseModel):
    """Dataset view request with filters"""
    dataset_id: UUID
    limit: int = 100
    offset: int = 0
    filters: Optional[dict] = None  # Field-based filters, e.g., {"lob": "COMMERCIAL", "cpt_code": ["72148"]}


class DatasetRow(BaseModel):
    """Single dataset row"""
    data: dict  # Flexible row data structure


@router.get("/datasets/{dataset_id}/view")
async def view_dataset(
    dataset_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    # Filter parameters
    lob: Optional[str] = Query(None),
    market: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    cpt_code: Optional[str] = Query(None),  # Single code or comma-separated
    place_of_service: Optional[str] = Query(None),
    service_category: Optional[str] = Query(None),
    member_id: Optional[str] = Query(None),
    provider_id: Optional[str] = Query(None),
):
    """
    View dataset rows with filtering capabilities
    Queries Parquet files from object storage with applied filters
    """
    try:
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.tenant_id == current_user.tenant_id,
        ).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Query Parquet file from object storage
        settings = get_settings()
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.object_storage.endpoint,
            aws_access_key_id=settings.object_storage.access_key,
            aws_secret_access_key=settings.object_storage.secret_key,
            region_name=settings.object_storage.region,
            use_ssl=settings.object_storage.use_ssl,
        )
        
        bucket = settings.object_storage.bucket
        
        # Parse S3 URI
        if dataset.data_uri.startswith("s3://"):
            parts = dataset.data_uri.replace("s3://", "").split("/", 1)
            file_key = parts[1] if len(parts) > 1 else ""
        else:
            file_key = dataset.data_uri
        
        # Download and read Parquet file
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp:
                s3_client.download_fileobj(bucket, file_key, tmp)
                tmp_path = tmp.name
            
            # Read Parquet with Polars
            df = pl.read_parquet(tmp_path)
            
            # Apply filters
            if lob and "lob" in df.columns:
                df = df.filter(pl.col("lob") == lob)
            
            if market and "market" in df.columns:
                df = df.filter(pl.col("market") == market)
            
            if year:
                if "year" in df.columns:
                    df = df.filter(pl.col("year") == year)
                elif "service_date" in df.columns or "enrollment_month" in df.columns:
                    date_col = "service_date" if "service_date" in df.columns else "enrollment_month"
                    if df[date_col].dtype == pl.Utf8:
                        df = df.with_columns(pl.col(date_col).str.strptime(pl.Date, "%Y-%m-%d"))
                    df = df.filter(pl.col(date_col).dt.year() == year)
            
            if month:
                if "month" in df.columns:
                    df = df.filter(pl.col("month") == month)
                elif "service_date" in df.columns or "enrollment_month" in df.columns:
                    date_col = "service_date" if "service_date" in df.columns else "enrollment_month"
                    if df[date_col].dtype == pl.Utf8:
                        df = df.with_columns(pl.col(date_col).str.strptime(pl.Date, "%Y-%m-%d"))
                    df = df.filter(pl.col(date_col).dt.month() == month)
            
            if cpt_code:
                codes = [c.strip() for c in cpt_code.split(",")]
                cpt_col = "cpt_code" if "cpt_code" in df.columns else ("cpt_hcpcs" if "cpt_hcpcs" in df.columns else None)
                if cpt_col and cpt_col in df.columns:
                    df = df.filter(pl.col(cpt_col).is_in(codes))
            
            if place_of_service:
                pos_col = "place_of_service" if "place_of_service" in df.columns else ("pos_code" if "pos_code" in df.columns else None)
                if pos_col and pos_col in df.columns:
                    df = df.filter(pl.col(pos_col) == place_of_service)
            
            if service_category and "service_category" in df.columns:
                df = df.filter(pl.col("service_category") == service_category)
            
            if member_id and "member_id" in df.columns:
                df = df.filter(pl.col("member_id") == member_id)
            
            if provider_id and "provider_id" in df.columns:
                df = df.filter(pl.col("provider_id") == provider_id)
            
            # Get total count before pagination
            total_count = len(df)
            
            # Apply pagination
            df_paginated = df.slice(offset, limit)
            
            # Convert to list of dicts
            rows = df_paginated.to_dicts()
            
            return {
                "dataset_id": str(dataset_id),
                "dataset_type": dataset.dataset_type,
                "year": dataset.year,
                "month": dataset.month,
                "lob": dataset.lob,
                "market": dataset.market,
                "filters_applied": {
                    "lob": lob,
                    "market": market,
                    "year": year,
                    "month": month,
                    "cpt_code": cpt_code,
                    "place_of_service": place_of_service,
                    "service_category": service_category,
                    "member_id": member_id,
                    "provider_id": provider_id,
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_count,
                },
                "rows": rows,
            }
        except FileNotFoundError:
            # Parquet file doesn't exist - return empty result
            return {
                "dataset_id": str(dataset_id),
                "dataset_type": dataset.dataset_type,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": 0,
                },
                "rows": [],
                "message": "Dataset file not found in object storage",
            }
        finally:
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error querying dataset: {e}")
        import traceback
        traceback.print_exc()
        # Return metadata even if query fails
        return {
            "dataset_id": str(dataset_id),
            "dataset_type": dataset.dataset_type if dataset else "UNKNOWN",
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": 0,
            },
            "rows": [],
            "error": str(e),
        }


@router.get("/datasets/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get schema/column information for a dataset"""
    try:
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.tenant_id == current_user.tenant_id,
        ).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Return schema based on dataset type
        schemas = {
            "CLAIMS": {
                "columns": [
                    {"name": "claim_id", "type": "string"},
                    {"name": "claim_line_id", "type": "string"},
                    {"name": "member_id", "type": "string"},
                    {"name": "provider_id", "type": "string"},
                    {"name": "service_date", "type": "date"},
                    {"name": "paid_date", "type": "date"},
                    {"name": "lob", "type": "string"},
                    {"name": "market", "type": "string"},
                    {"name": "cpt_code", "type": "string"},
                    {"name": "service_category", "type": "string"},
                    {"name": "place_of_service", "type": "string"},
                    {"name": "units", "type": "float"},
                    {"name": "allowed_amount", "type": "float"},
                    {"name": "paid_amount", "type": "float"},
                    {"name": "in_network", "type": "boolean"},
                ],
            },
            "ENROLLMENT": {
                "columns": [
                    {"name": "member_id", "type": "string"},
                    {"name": "lob", "type": "string"},
                    {"name": "market", "type": "string"},
                    {"name": "enrollment_month", "type": "date"},
                    {"name": "age_band", "type": "string"},
                    {"name": "gender", "type": "string"},
                    {"name": "risk_score", "type": "float"},
                    {"name": "network_tier", "type": "string"},
                    {"name": "enrolled_flag", "type": "boolean"},
                ],
            },
            "PROVIDERS": {
                "columns": [
                    {"name": "provider_id", "type": "string"},
                    {"name": "npi", "type": "string"},
                    {"name": "provider_type", "type": "string"},
                    {"name": "specialty", "type": "string"},
                    {"name": "facility_type", "type": "string"},
                    {"name": "market", "type": "string"},
                    {"name": "network_status", "type": "string"},
                    {"name": "system_affiliation", "type": "string"},
                ],
            },
        }
        
        schema = schemas.get(dataset.dataset_type, {"columns": []})
        
        return {
            "dataset_id": str(dataset_id),
            "dataset_type": dataset.dataset_type,
            "schema": schema,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dataset schema: {str(e)}")

