"""Datasets routes using file storage (for local development)"""
from typing import Annotated, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from pathlib import Path
import json

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_ingestions import list_ingestions

router = APIRouter()


@router.get("/datasets")
async def get_datasets(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    dataset_type: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    lob: Optional[str] = Query(None),
    market: Optional[str] = Query(None),
):
    """List available datasets from ingestions"""
    # Get all completed ingestions
    ingestions = list_ingestions(current_user.tenant_id)
    completed_ingestions = [ing for ing in ingestions if ing.get("status") == "COMPLETED"]
    
    # Convert ingestions to dataset format
    datasets = []
    for ingestion in completed_ingestions:
        metadata = ingestion.get("metadata", {})
        processing_result = metadata.get("processing_result", {})
        
        # Extract dataset info from ingestion metadata
        dataset = {
            "id": ingestion.get("id"),
            "tenant_id": str(ingestion.get("tenant_id")),
            "dataset_type": ingestion.get("ingestion_type", "CLAIMS"),
            "year": metadata.get("year"),
            "month": metadata.get("month"),
            "lob": metadata.get("lob"),
            "market": metadata.get("market"),
            "record_count": processing_result.get("records_valid") or metadata.get("records_processed", 0),
            "data_uri": ingestion.get("manifest_uri", ""),
            "created_at": ingestion.get("created_at"),
            "updated_at": ingestion.get("updated_at"),
        }
        
        # Apply filters
        if dataset_type and dataset.get("dataset_type") != dataset_type:
            continue
        if year and dataset.get("year") != year:
            continue
        if month and dataset.get("month") != month:
            continue
        if lob and dataset.get("lob") != lob:
            continue
        if market and dataset.get("market") != market:
            continue
        
        datasets.append(dataset)
    
    return datasets


@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a specific dataset by ID"""
    ingestion = None
    ingestions = list_ingestions(current_user.tenant_id)
    for ing in ingestions:
        if str(ing.get("id")) == str(dataset_id):
            ingestion = ing
            break
    
    if not ingestion:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    metadata = ingestion.get("metadata", {})
    processing_result = metadata.get("processing_result", {})
    
    return {
        "id": ingestion.get("id"),
        "tenant_id": str(ingestion.get("tenant_id")),
        "dataset_type": ingestion.get("ingestion_type", "CLAIMS"),
        "year": metadata.get("year"),
        "month": metadata.get("month"),
        "lob": metadata.get("lob"),
        "market": metadata.get("market"),
        "record_count": processing_result.get("records_valid") or metadata.get("records_processed", 0),
        "data_uri": ingestion.get("manifest_uri", ""),
        "created_at": ingestion.get("created_at"),
        "updated_at": ingestion.get("updated_at"),
    }


@router.get("/datasets/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get schema for a dataset"""
    # For now, return a basic schema based on dataset type
    ingestion = None
    ingestions = list_ingestions(current_user.tenant_id)
    for ing in ingestions:
        if str(ing.get("id")) == str(dataset_id):
            ingestion = ing
            break
    
    if not ingestion:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset_type = ingestion.get("ingestion_type", "CLAIMS")
    
    # Return schema based on dataset type
    if dataset_type == "CLAIMS":
        return {
            "fields": [
                {"name": "claim_id", "type": "string", "required": True},
                {"name": "claim_line_id", "type": "string", "required": True},
                {"name": "member_id", "type": "string", "required": True},
                {"name": "service_from_date", "type": "date", "required": True},
                {"name": "lob", "type": "string", "required": True},
                {"name": "market", "type": "string", "required": True},
                {"name": "cpt_hcpcs", "type": "string", "required": True},
                {"name": "rendering_npi", "type": "string", "required": True},
                {"name": "allowed_amount", "type": "float", "required": True},
                {"name": "paid_amount", "type": "float", "required": True},
            ]
        }
    elif dataset_type == "ENROLLMENT":
        return {
            "fields": [
                {"name": "member_id", "type": "string", "required": True},
                {"name": "lob", "type": "string", "required": True},
                {"name": "market", "type": "string", "required": True},
                {"name": "enrolled_flag", "type": "bool", "required": True},
            ]
        }
    elif dataset_type == "PROVIDERS":
        return {
            "fields": [
                {"name": "npi", "type": "string", "required": True},
                {"name": "provider_name", "type": "string", "required": True},
                {"name": "specialty", "type": "string", "required": True},
                {"name": "market", "type": "string", "required": True},
            ]
        }
    else:
        return {"fields": []}


@router.get("/datasets/{dataset_id}/view")
async def view_dataset(
    dataset_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    lob: Optional[str] = Query(None),
    market: Optional[str] = Query(None),
):
    """View dataset data with filtering"""
    # For file storage mode, we'll return metadata about the dataset
    # Actual data viewing would require reading from the stored files
    ingestion = None
    ingestions = list_ingestions(current_user.tenant_id)
    for ing in ingestions:
        if str(ing.get("id")) == str(dataset_id):
            ingestion = ing
            break
    
    if not ingestion:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    metadata = ingestion.get("metadata", {})
    
    # Return sample data structure (in real implementation, would read from file)
    return {
        "dataset_id": str(dataset_id),
        "total_records": metadata.get("records_processed", 0),
        "limit": limit,
        "offset": offset,
        "rows": [],  # Would contain actual data rows
        "message": "Data viewing from file storage is in progress. Use ingestion details to access data.",
    }

