"""Cohort endpoints - File storage only (returns empty for now)"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, verify_token

router = APIRouter()


class CohortCreate(BaseModel):
    """Cohort creation model"""
    name: str
    description: str | None = None
    criteria: dict  # FilterSpec


class CohortResponse(BaseModel):
    """Cohort response model"""
    id: UUID
    name: str
    description: str | None
    criteria: dict
    member_count: int | None = None
    created_at: str | None = None


@router.get("/cohorts", response_model=list[CohortResponse])
async def list_cohorts(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List cohorts - File storage only (returns empty list)"""
    # File storage mode - cohorts not yet implemented
    return []


@router.post("/cohorts", response_model=CohortResponse, status_code=201)
async def create_cohort(
    cohort_data: CohortCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Create cohort - File storage only (returns error)"""
    # File storage mode - cohorts not yet implemented
    raise HTTPException(status_code=503, detail="Cohort creation not available in file-storage mode")


@router.get("/cohorts/{cohort_id}", response_model=CohortResponse)
async def get_cohort(
    cohort_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get cohort - File storage only (returns 404)"""
    # File storage mode - cohorts not yet implemented
    raise HTTPException(status_code=404, detail="Cohort not found")


@router.delete("/cohorts/{cohort_id}", status_code=204)
async def delete_cohort(
    cohort_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Delete cohort - File storage only (returns 404)"""
    # File storage mode - cohorts not yet implemented
    raise HTTPException(status_code=404, detail="Cohort not found")


@router.get("/cohorts/{cohort_id}/members")
async def get_cohort_members(
    cohort_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get cohort members - File storage only (returns 404)"""
    # File storage mode - cohorts not yet implemented
    raise HTTPException(status_code=404, detail="Cohort not found")
