"""Data period endpoints - File storage only"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.storage_data_periods import (
    create_data_period,
    get_data_period,
    list_data_periods,
    update_data_period,
    get_baseline_eligible_periods,
    get_latest_baseline_period,
)

router = APIRouter()


class DataPeriodCreate(BaseModel):
    """Data period creation model"""
    period_type: str = "MONTHLY"  # MONTHLY, QUARTERLY, YEARLY
    start_date: str
    end_date: str
    ingestion_id: Optional[str] = None
    data_status: str = "COMPLETE"  # COMPLETE, PARTIAL, STALE
    baseline_eligible: bool = True
    policies_effective: Optional[list[str]] = None
    metadata: Optional[dict] = None


class DataPeriodUpdate(BaseModel):
    """Data period update model"""
    data_status: Optional[str] = None
    baseline_eligible: Optional[bool] = None
    policies_effective: Optional[list[str]] = None
    metadata: Optional[dict] = None


@router.post("/periods", status_code=201)
async def create_period(
    period_data: DataPeriodCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Create a new data period"""
    period_doc = create_data_period(
        tenant_id=current_user.tenant_id,
        period_data=period_data.model_dump(exclude_none=True),
    )
    return period_doc


@router.get("/periods")
async def list_periods(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    period_type: Optional[str] = Query(None),
    baseline_eligible: Optional[bool] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """List data periods for the current tenant"""
    periods = list_data_periods(
        tenant_id=current_user.tenant_id,
        period_type=period_type,
        baseline_eligible=baseline_eligible,
        start_date=start_date,
        end_date=end_date,
    )
    return periods


@router.get("/periods/{period_id}")
async def get_period(
    period_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get a data period by ID"""
    period = get_data_period(current_user.tenant_id, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Data period not found")
    return period


@router.put("/periods/{period_id}")
async def update_period(
    period_id: str,
    period_data: DataPeriodUpdate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Update a data period"""
    updates = period_data.model_dump(exclude_none=True)
    period = update_data_period(
        tenant_id=current_user.tenant_id,
        period_id=period_id,
        updates=updates,
    )
    if not period:
        raise HTTPException(status_code=404, detail="Data period not found")
    return period


@router.get("/periods/baseline-eligible")
async def get_baseline_eligible(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    policy_effective_date: Optional[str] = Query(None),
):
    """Get baseline-eligible periods (pre-policy data)"""
    periods = get_baseline_eligible_periods(
        tenant_id=current_user.tenant_id,
        policy_effective_date=policy_effective_date,
    )
    return periods


@router.get("/periods/baseline-eligible/latest")
async def get_latest_baseline(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    policy_effective_date: Optional[str] = Query(None),
):
    """Get the latest baseline-eligible period"""
    period = get_latest_baseline_period(
        tenant_id=current_user.tenant_id,
        policy_effective_date=policy_effective_date,
    )
    if not period:
        raise HTTPException(status_code=404, detail="No baseline-eligible periods found")
    return period
