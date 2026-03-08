"""Decision endpoints - File storage only (returns empty for now)"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, verify_token

router = APIRouter()


class DecisionCreate(BaseModel):
    """Decision creation model"""
    policy_id: UUID
    recommendation: str
    rationale: str | None = None
    action: str  # APPROVE, DENY, DEFER, REVIEW
    effective_date: str | None = None
    expiration_date: str | None = None


class DecisionResponse(BaseModel):
    """Decision response model"""
    id: UUID
    policy_id: UUID
    recommendation: str
    rationale: str | None
    action: str
    status: str
    created_at: str | None = None
    updated_at: str | None = None


@router.post("/decisions", response_model=DecisionResponse, status_code=201)
async def create_decision(
    decision_data: DecisionCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Create decision - File storage only (returns error)"""
    # File storage mode - decisions not yet implemented
    raise HTTPException(status_code=503, detail="Decision creation not available in file-storage mode")


@router.get("/decisions", response_model=list[DecisionResponse])
async def list_decisions(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    quarter: str | None = Query(None),
    status: str | None = Query(None),
    lob: str | None = Query(None),
    market: str | None = Query(None),
    owner: UUID | None = Query(None),
):
    """List decisions - File storage only (returns empty list)"""
    # File storage mode - decisions not yet implemented
    return []


@router.get("/decisions/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get decision - File storage only (returns 404)"""
    # File storage mode - decisions not yet implemented
    raise HTTPException(status_code=404, detail="Decision not found")


@router.patch("/decisions/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: UUID,
    decision_data: dict,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Update decision - File storage only (returns 404)"""
    # File storage mode - decisions not yet implemented
    raise HTTPException(status_code=404, detail="Decision not found")
