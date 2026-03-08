"""Notification endpoints - File storage only (returns empty for now)"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, verify_token

router = APIRouter()


@router.get("/notifications")
async def list_notifications(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    unread_only: bool = Query(False),
):
    """List notifications - File storage only (returns empty list)"""
    # File storage mode - notifications not yet implemented
    return []


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Mark notification as read - File storage only (returns 404)"""
    # File storage mode - notifications not yet implemented
    raise HTTPException(status_code=404, detail="Notification not found")


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Delete notification - File storage only (returns 404)"""
    # File storage mode - notifications not yet implemented
    raise HTTPException(status_code=404, detail="Notification not found")
