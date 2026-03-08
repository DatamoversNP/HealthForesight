"""
Epic 6: Collaboration Workflows - API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID

from uepi_api.auth import get_demo_current_user, CurrentUser
from uepi_api.storage_collaboration import (
    create_comment,
    get_comment,
    list_comments,
    create_task,
    get_task,
    list_tasks,
    create_approval_request,
    get_approval_request,
    list_approval_requests,
    create_activity_event,
    list_activity_events,
)
from uepi_common.models_enhanced import ResourceType

router = APIRouter()


def convert_resource_id_to_uuid(resource_id: str, resource_type: Optional[str] = None) -> Optional[UUID]:
    """Convert string resource ID to UUID, handling policy IDs specially"""
    if not resource_id:
        return None
    # Try UUID first
    try:
        return UUID(resource_id)
    except ValueError:
        # Not a UUID - if it's a POLICY resource, look up the policy
        if resource_type == "POLICY":
            from uepi_api.storage_policies import list_policies
            # We need tenant_id, but we'll handle this in the endpoint
            # For now, return None and let the endpoint handle it
            return None
        # For other resource types, generate deterministic UUID
        import hashlib
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return UUID(bytes=hashlib.md5(namespace.bytes + resource_id.encode()).digest())


# Comments
@router.post("/comments")
async def create_comment_endpoint(
    comment_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new comment"""
    try:
        if "user_id" not in comment_data:
            comment_data["user_id"] = str(current_user.user_id)
        comment = create_comment(
            tenant_id=current_user.tenant_id,
            comment_data=comment_data,
        )
        return comment.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create comment: {str(e)}")


@router.get("/comments")
async def list_comments_endpoint(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List comments"""
    try:
        rt = ResourceType(resource_type) if resource_type else None
        rid = None
        if resource_id:
            try:
                rid = UUID(resource_id)
            except ValueError:
                # Not a UUID - generate deterministic UUID (fast, no lookup)
                import hashlib
                namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
                rid = UUID(bytes=hashlib.md5(namespace.bytes + resource_id.encode()).digest())
        comments = list_comments(
            tenant_id=current_user.tenant_id,
            resource_type=rt,
            resource_id=rid,
        )
        return [c.model_dump(mode='json', exclude_none=True) for c in comments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list comments: {str(e)}")


@router.get("/comments/{comment_id}")
async def get_comment_endpoint(
    comment_id: str,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Get comment"""
    try:
        comment_uuid = UUID(comment_id)
        comment = get_comment(
            tenant_id=current_user.tenant_id,
            comment_id=comment_uuid,
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        return comment.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid comment ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comment: {str(e)}")


# Tasks
@router.post("/tasks")
async def create_task_endpoint(
    task_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new task"""
    try:
        if "assigned_by" not in task_data:
            task_data["assigned_by"] = str(current_user.user_id)
        task = create_task(
            tenant_id=current_user.tenant_id,
            task_data=task_data,
        )
        return task.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/tasks")
async def list_tasks_endpoint(
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List tasks"""
    try:
        assigned_uuid = UUID(assigned_to) if assigned_to else None
        tasks = list_tasks(
            tenant_id=current_user.tenant_id,
            assigned_to=assigned_uuid,
            status=status,
        )
        return [t.model_dump(mode='json', exclude_none=True) for t in tasks]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assigned_to ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task_endpoint(
    task_id: str,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Get task"""
    try:
        task_uuid = UUID(task_id)
        task = get_task(
            tenant_id=current_user.tenant_id,
            task_id=task_uuid,
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


# Approval Requests
@router.post("/approvals")
async def create_approval_request_endpoint(
    request_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new approval request"""
    try:
        if "requested_by" not in request_data:
            request_data["requested_by"] = str(current_user.user_id)
        request = create_approval_request(
            tenant_id=current_user.tenant_id,
            request_data=request_data,
        )
        return request.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create approval request: {str(e)}")


@router.get("/approvals")
async def list_approval_requests_endpoint(
    resource_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List approval requests"""
    try:
        rid = UUID(resource_id) if resource_id else None
        requests = list_approval_requests(
            tenant_id=current_user.tenant_id,
            resource_id=rid,
            status=status,
        )
        return [r.model_dump(mode='json', exclude_none=True) for r in requests]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resource ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list approval requests: {str(e)}")


@router.get("/approvals/{request_id}")
async def get_approval_request_endpoint(
    request_id: str,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Get approval request"""
    try:
        request_uuid = UUID(request_id)
        request = get_approval_request(
            tenant_id=current_user.tenant_id,
            request_id=request_uuid,
        )
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")
        return request.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approval request: {str(e)}")


# Activity Events
@router.post("/activity")
async def create_activity_event_endpoint(
    event_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new activity event"""
    try:
        if "user_id" not in event_data:
            event_data["user_id"] = str(current_user.user_id)
        event = create_activity_event(
            tenant_id=current_user.tenant_id,
            event_data=event_data,
        )
        return event.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create activity event: {str(e)}")


@router.get("/activity")
async def list_activity_events_endpoint(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    limit: int = 100,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List activity events"""
    try:
        rt = ResourceType(resource_type) if resource_type else None
        rid = None
        if resource_id:
            try:
                rid = UUID(resource_id)
            except ValueError:
                # Not a UUID - generate deterministic UUID (fast, no lookup)
                import hashlib
                namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
                rid = UUID(bytes=hashlib.md5(namespace.bytes + resource_id.encode()).digest())
        events = list_activity_events(
            tenant_id=current_user.tenant_id,
            resource_type=rt,
            resource_id=rid,
            limit=limit,
        )
        return [e.model_dump(mode='json', exclude_none=True) for e in events]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list activity events: {str(e)}")

