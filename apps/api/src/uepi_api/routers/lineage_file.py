"""Lineage endpoints - File storage only (returns empty for now)"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, verify_token

router = APIRouter()


@router.get("/lineage/coverage")
async def get_data_coverage(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get data coverage - File storage only (returns empty)"""
    # File storage mode - lineage not yet implemented
    return {"coverage": {}}


@router.get("/lineage/ingestions")
async def list_recent_ingestions(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """List recent ingestions - File storage only (returns empty list)"""
    # File storage mode - lineage not yet implemented
    return []


@router.get("/lineage/analyses")
async def list_analysis_runs(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """List analysis runs - File storage only (returns empty list)"""
    # File storage mode - lineage not yet implemented
    return []
