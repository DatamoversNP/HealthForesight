"""Notifications API endpoints"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_notifications import (
    create_notification as create_notification_storage,
    list_notifications as list_notifications_storage,
    mark_notification_read as mark_notification_read_storage,
    mark_all_read as mark_all_read_storage,
    get_unread_count as get_unread_count_storage,
)

router = APIRouter()


@router.get("/notifications")
async def list_notifications(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
):
    """List notifications for the current user"""
    try:
        user_id = current_user.user_id if hasattr(current_user, 'user_id') else None
        # Convert user_id to UUID if it's not already
        user_id_uuid = None
        if user_id:
            if isinstance(user_id, UUID):
                user_id_uuid = user_id
            else:
                try:
                    user_id_uuid = UUID(str(user_id))
                except (ValueError, TypeError):
                    user_id_uuid = None
        
        notifications = list_notifications_storage(
            tenant_id=current_user.tenant_id,
            user_id=user_id_uuid,
            unread_only=unread_only,
            limit=limit,
        )
        return notifications
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list notifications: {str(e)}")


@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get count of unread notifications"""
    try:
        user_id = current_user.user_id if hasattr(current_user, 'user_id') else None
        # Convert user_id to UUID if it's not already
        user_id_uuid = None
        if user_id:
            if isinstance(user_id, UUID):
                user_id_uuid = user_id
            else:
                try:
                    user_id_uuid = UUID(str(user_id))
                except (ValueError, TypeError):
                    user_id_uuid = None
        
        count = get_unread_count_storage(
            tenant_id=current_user.tenant_id,
            user_id=user_id_uuid,
        )
        return {"count": count}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Mark a notification as read"""
    try:
        notification = mark_notification_read_storage(notification_id, current_user.tenant_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Mark all notifications as read"""
    try:
        user_id = current_user.user_id if hasattr(current_user, 'user_id') else None
        # Convert user_id to UUID if it's not already
        user_id_uuid = None
        if user_id:
            if isinstance(user_id, UUID):
                user_id_uuid = user_id
            else:
                try:
                    user_id_uuid = UUID(str(user_id))
                except (ValueError, TypeError):
                    user_id_uuid = None
        
        count = mark_all_read_storage(
            tenant_id=current_user.tenant_id,
            user_id=user_id_uuid,
        )
        return {"message": f"Marked {count} notifications as read"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to mark all as read: {str(e)}")
