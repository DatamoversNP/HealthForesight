"""Scheduled jobs API endpoints"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_schedules import (
    create_schedule as create_schedule_storage,
    get_schedule as get_schedule_storage,
    list_schedules as list_schedules_storage,
    update_schedule as update_schedule_storage,
    delete_schedule as delete_schedule_storage,
)

router = APIRouter()


class ScheduleCreate(BaseModel):
    name: str
    schedule_type: str  # EXPORT, ANALYSIS, OBSERVATION
    frequency: str  # DAILY, WEEKLY, MONTHLY
    time: str  # HH:MM format
    day_of_week: Optional[int] = None  # For weekly (0-6)
    day_of_month: Optional[int] = None  # For monthly (1-31)
    config: dict = {}  # Schedule-specific config
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    frequency: Optional[str] = None
    time: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None


@router.post("/schedules", status_code=201)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new scheduled job"""
    try:
        schedule = create_schedule_storage(
            tenant_id=current_user.tenant_id,
            schedule_data={
                **schedule_data.dict(),
                "created_by": str(current_user.user_id) if hasattr(current_user, 'user_id') else None,
            },
        )
        return schedule
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.get("/schedules")
async def list_schedules(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """List all schedules for the tenant"""
    try:
        schedules = list_schedules_storage(current_user.tenant_id)
        return schedules
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list schedules: {str(e)}")


@router.get("/schedules/{schedule_id}")
async def get_schedule(
    schedule_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a schedule by ID"""
    try:
        schedule = get_schedule_storage(schedule_id, current_user.tenant_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return schedule
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get schedule: {str(e)}")


@router.put("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: UUID,
    schedule_update: ScheduleUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update a schedule"""
    try:
        updates = {k: v for k, v in schedule_update.dict().items() if v is not None}
        schedule = update_schedule_storage(schedule_id, current_user.tenant_id, updates)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return schedule
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update schedule: {str(e)}")


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Delete a schedule"""
    try:
        deleted = delete_schedule_storage(schedule_id, current_user.tenant_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return {"message": "Schedule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")
