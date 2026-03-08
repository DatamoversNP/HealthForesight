"""
Epic 6: Collaboration Workflows - Storage Module
Database only
"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.collaboration import Comment as CommentDB, Task as TaskDB, Approval as ApprovalDB, ActivityEvent as ActivityEventDB
from uepi_common.models_enhanced import (
    Comment,
    Task,
    ApprovalRequest,
    ActivityEvent,
    ResourceType,
)
from sqlalchemy import desc


def _safe_uuid(value: Any) -> Optional[UUID]:
    """Safely convert value to UUID"""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return UUID(value)
        except (ValueError, AttributeError):
            return None
    return None


# Comments
def create_comment(
    tenant_id: UUID,
    comment_data: Dict[str, Any]
) -> Comment:
    """Create a new comment - stored in database"""
    return _create_comment(tenant_id, comment_data)


def _create_comment(
    tenant_id: UUID,
    comment_data: Dict[str, Any]
) -> Comment:
    """Create comment in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        comment_db = CommentDB(
            tenant_id=tenant_id,
            resource_type=comment_data.get("resource_type", "POLICY").value if isinstance(comment_data.get("resource_type"), ResourceType) else str(comment_data.get("resource_type", "POLICY")),
            resource_id=str(_safe_uuid(comment_data.get("resource_id")) or uuid4()),
            user_id=_safe_uuid(comment_data.get("user_id")) or uuid4(),
            content=comment_data.get("content", ""),
        )
        
        db.add(comment_db)
        db.commit()
        db.refresh(comment_db)
        
        # Return Pydantic model for compatibility
        return Comment(
            comment_id=comment_db.id,
            resource_type=ResourceType(comment_db.resource_type),
            resource_id=UUID(comment_db.resource_id) if comment_db.resource_id else uuid4(),
            user_id=comment_db.user_id,
            content=comment_db.content,
            mentions=[],  # Not stored in DB model
            parent_comment_id=None,  # Not stored in DB model
            created_at=comment_db.created_at,
            updated_at=comment_db.updated_at,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create comment: {e}")
    finally:
        db.close()


def get_comment(
    tenant_id: UUID,
    comment_id: UUID
) -> Optional[Comment]:
    """Get comment - from database"""
    return _get_comment(tenant_id, comment_id)


def _get_comment(
    tenant_id: UUID,
    comment_id: UUID
) -> Optional[Comment]:
    """Get comment from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        comment_db = db.query(CommentDB).filter(
            CommentDB.tenant_id == tenant_id,
            CommentDB.id == comment_id
        ).first()
        
        if not comment_db:
            return None
        
        # Return Pydantic model for compatibility
        return Comment(
            comment_id=comment_db.id,
            resource_type=ResourceType(comment_db.resource_type),
            resource_id=UUID(comment_db.resource_id) if comment_db.resource_id else uuid4(),
            user_id=comment_db.user_id,
            content=comment_db.content,
            mentions=[],  # Not stored in DB model
            parent_comment_id=None,  # Not stored in DB model
            created_at=comment_db.created_at,
            updated_at=comment_db.updated_at,
        )
        
    except Exception as e:
        print(f"ERROR get_comment (DB): {e}")
        return None
    finally:
        db.close()


def list_comments(
    tenant_id: UUID,
    resource_type: Optional[ResourceType] = None,
    resource_id: Optional[UUID] = None
) -> List[Comment]:
    """List comments - from database"""
    return _list_comments(tenant_id, resource_type, resource_id)


def _list_comments(
    tenant_id: UUID,
    resource_type: Optional[ResourceType] = None,
    resource_id: Optional[UUID] = None
) -> List[Comment]:
    """List comments from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(CommentDB).filter(CommentDB.tenant_id == tenant_id)
        
        # Filter by resource_type if provided
        if resource_type:
            query = query.filter(CommentDB.resource_type == resource_type.value)
        
        # Filter by resource_id if provided
        if resource_id:
            query = query.filter(CommentDB.resource_id == str(resource_id))
        
        # Sort by created_at descending
        comments_db = query.order_by(desc(CommentDB.created_at)).all()
        
        # Convert to Pydantic models for compatibility
        result = []
        for comment_db in comments_db:
            result.append(Comment(
                comment_id=comment_db.id,
                resource_type=ResourceType(comment_db.resource_type),
                resource_id=UUID(comment_db.resource_id) if comment_db.resource_id else uuid4(),
                user_id=comment_db.user_id,
                content=comment_db.content,
                mentions=[],  # Not stored in DB model
                parent_comment_id=None,  # Not stored in DB model
                created_at=comment_db.created_at,
                updated_at=comment_db.updated_at,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_comments (DB): {e}")
        return []
    finally:
        db.close()


# Tasks
def create_task(
    tenant_id: UUID,
    task_data: Dict[str, Any]
) -> Task:
    """Create a new task - stored in database"""
    return _create_task(tenant_id, task_data)


def _create_task(
    tenant_id: UUID,
    task_data: Dict[str, Any]
) -> Task:
    """Create task in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        task_db = TaskDB(
            tenant_id=tenant_id,
            resource_type=task_data.get("resource_type", "POLICY").value if isinstance(task_data.get("resource_type"), ResourceType) else str(task_data.get("resource_type", "POLICY")),
            resource_id=str(_safe_uuid(task_data.get("resource_id")) or uuid4()),
            title=task_data.get("title", ""),
            description=task_data.get("description", ""),
            assigned_to_user_id=_safe_uuid(task_data.get("assigned_to")),
            status=task_data.get("status", "OPEN"),
            due_date=datetime.fromisoformat(task_data["due_date"].replace("Z", "+00:00")) if isinstance(task_data.get("due_date"), str) else task_data.get("due_date"),
            priority=task_data.get("priority"),
        )
        
        db.add(task_db)
        db.commit()
        db.refresh(task_db)
        
        # Return Pydantic model for compatibility
        return Task(
            task_id=task_db.id,
            resource_type=ResourceType(task_db.resource_type),
            resource_id=UUID(task_db.resource_id) if task_db.resource_id else uuid4(),
            title=task_db.title,
            description=task_db.description,
            assigned_to=task_db.assigned_to_user_id,
            assigned_by=uuid4(),  # Not stored in DB model
            due_date=task_db.due_date,
            status=task_db.status,
            created_at=task_db.created_at,
            completed_at=task_db.completed_at,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create task: {e}")
    finally:
        db.close()


def get_task(
    tenant_id: UUID,
    task_id: UUID
) -> Optional[Task]:
    """Get task - from database"""
    return _get_task(tenant_id, task_id)


def _get_task(
    tenant_id: UUID,
    task_id: UUID
) -> Optional[Task]:
    """Get task from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        task_db = db.query(TaskDB).filter(
            TaskDB.tenant_id == tenant_id,
            TaskDB.id == task_id
        ).first()
        
        if not task_db:
            return None
        
        # Return Pydantic model for compatibility
        return Task(
            task_id=task_db.id,
            resource_type=ResourceType(task_db.resource_type),
            resource_id=UUID(task_db.resource_id) if task_db.resource_id else uuid4(),
            title=task_db.title,
            description=task_db.description,
            assigned_to=task_db.assigned_to_user_id,
            assigned_by=uuid4(),  # Not stored in DB model
            due_date=task_db.due_date,
            status=task_db.status,
            created_at=task_db.created_at,
            completed_at=task_db.completed_at,
        )
        
    except Exception as e:
        print(f"ERROR get_task (DB): {e}")
        return None
    finally:
        db.close()


def list_tasks(
    tenant_id: UUID,
    assigned_to: Optional[UUID] = None,
    status: Optional[str] = None
) -> List[Task]:
    """List tasks - from database"""
    return _list_tasks(tenant_id, assigned_to, status)


def _list_tasks(
    tenant_id: UUID,
    assigned_to: Optional[UUID] = None,
    status: Optional[str] = None
) -> List[Task]:
    """List tasks from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(TaskDB).filter(TaskDB.tenant_id == tenant_id)
        
        # Filter by assigned_to if provided
        if assigned_to:
            query = query.filter(TaskDB.assigned_to_user_id == assigned_to)
        
        # Filter by status if provided
        if status:
            query = query.filter(TaskDB.status == status)
        
        # Sort by created_at descending
        tasks_db = query.order_by(desc(TaskDB.created_at)).all()
        
        # Convert to Pydantic models for compatibility
        result = []
        for task_db in tasks_db:
            result.append(Task(
                task_id=task_db.id,
                resource_type=ResourceType(task_db.resource_type),
                resource_id=UUID(task_db.resource_id) if task_db.resource_id else uuid4(),
                title=task_db.title,
                description=task_db.description,
                assigned_to=task_db.assigned_to_user_id,
                assigned_by=uuid4(),  # Not stored in DB model
                due_date=task_db.due_date,
                status=task_db.status,
                created_at=task_db.created_at,
                completed_at=task_db.completed_at,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_tasks (DB): {e}")
        return []
    finally:
        db.close()


# Approval Requests
def create_approval_request(
    tenant_id: UUID,
    request_data: Dict[str, Any]
) -> ApprovalRequest:
    """Create a new approval request - stored in database"""
    return _create_approval_request(tenant_id, request_data)


def _create_approval_request(
    tenant_id: UUID,
    request_data: Dict[str, Any]
) -> ApprovalRequest:
    """Create approval request in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        approval_db = ApprovalDB(
            tenant_id=tenant_id,
            resource_type=request_data.get("resource_type", "POLICY").value if isinstance(request_data.get("resource_type"), ResourceType) else str(request_data.get("resource_type", "POLICY")),
            resource_id=str(_safe_uuid(request_data.get("resource_id")) or uuid4()),
            requested_by_user_id=_safe_uuid(request_data.get("requested_by")) or uuid4(),
            status=request_data.get("status", "PENDING"),
            reason=request_data.get("reason") or request_data.get("comments", ""),
        )
        
        db.add(approval_db)
        db.commit()
        db.refresh(approval_db)
        
        # Return Pydantic model for compatibility
        return ApprovalRequest(
            request_id=approval_db.id,
            resource_type=ResourceType(approval_db.resource_type),
            resource_id=UUID(approval_db.resource_id) if approval_db.resource_id else uuid4(),
            requested_by=approval_db.requested_by_user_id,
            requested_for=[],  # Not stored in DB model
            required_approvals=1,  # Not stored in DB model
            current_approvals=1 if approval_db.status == "APPROVED" else 0,
            status=approval_db.status,
            comments=[approval_db.reason] if approval_db.reason else [],
            created_at=approval_db.created_at,
            completed_at=approval_db.approved_at,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create approval request: {e}")
    finally:
        db.close()


def get_approval_request(
    tenant_id: UUID,
    request_id: UUID
) -> Optional[ApprovalRequest]:
    """Get approval request - from database"""
    return _get_approval_request(tenant_id, request_id)


def _get_approval_request(
    tenant_id: UUID,
    request_id: UUID
) -> Optional[ApprovalRequest]:
    """Get approval request from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        approval_db = db.query(ApprovalDB).filter(
            ApprovalDB.tenant_id == tenant_id,
            ApprovalDB.id == request_id
        ).first()
        
        if not approval_db:
            return None
        
        # Return Pydantic model for compatibility
        return ApprovalRequest(
            request_id=approval_db.id,
            resource_type=ResourceType(approval_db.resource_type),
            resource_id=UUID(approval_db.resource_id) if approval_db.resource_id else uuid4(),
            requested_by=approval_db.requested_by_user_id,
            requested_for=[],  # Not stored in DB model
            required_approvals=1,  # Not stored in DB model
            current_approvals=1 if approval_db.status == "APPROVED" else 0,
            status=approval_db.status,
            comments=[approval_db.reason] if approval_db.reason else [],
            created_at=approval_db.created_at,
            completed_at=approval_db.approved_at,
        )
        
    except Exception as e:
        print(f"ERROR get_approval_request (DB): {e}")
        return None
    finally:
        db.close()


def list_approval_requests(
    tenant_id: UUID,
    resource_id: Optional[UUID] = None,
    status: Optional[str] = None
) -> List[ApprovalRequest]:
    """List approval requests - from database"""
    return _list_approval_requests(tenant_id, resource_id, status)


def _list_approval_requests(
    tenant_id: UUID,
    resource_id: Optional[UUID] = None,
    status: Optional[str] = None
) -> List[ApprovalRequest]:
    """List approval requests from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(ApprovalDB).filter(ApprovalDB.tenant_id == tenant_id)
        
        # Filter by resource_id if provided
        if resource_id:
            query = query.filter(ApprovalDB.resource_id == str(resource_id))
        
        # Filter by status if provided
        if status:
            query = query.filter(ApprovalDB.status == status)
        
        # Sort by created_at descending
        approvals_db = query.order_by(desc(ApprovalDB.created_at)).all()
        
        # Convert to Pydantic models for compatibility
        result = []
        for approval_db in approvals_db:
            result.append(ApprovalRequest(
                request_id=approval_db.id,
                resource_type=ResourceType(approval_db.resource_type),
                resource_id=UUID(approval_db.resource_id) if approval_db.resource_id else uuid4(),
                requested_by=approval_db.requested_by_user_id,
                requested_for=[],  # Not stored in DB model
                required_approvals=1,  # Not stored in DB model
                current_approvals=1 if approval_db.status == "APPROVED" else 0,
                status=approval_db.status,
                comments=[approval_db.reason] if approval_db.reason else [],
                created_at=approval_db.created_at,
                completed_at=approval_db.approved_at,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_approval_requests (DB): {e}")
        return []
    finally:
        db.close()


# Activity Events
def create_activity_event(
    tenant_id: UUID,
    event_data: Dict[str, Any]
) -> ActivityEvent:
    """Create a new activity event - stored in database"""
    return _create_activity_event(tenant_id, event_data)


def _create_activity_event(
    tenant_id: UUID,
    event_data: Dict[str, Any]
) -> ActivityEvent:
    """Create activity event in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        activity_db = ActivityEventDB(
            tenant_id=tenant_id,
            resource_type=event_data.get("resource_type", "POLICY").value if isinstance(event_data.get("resource_type"), ResourceType) else str(event_data.get("resource_type", "POLICY")),
            resource_id=str(_safe_uuid(event_data.get("resource_id")) or uuid4()),
            user_id=_safe_uuid(event_data.get("user_id")),
            action=event_data.get("event_type", event_data.get("action", "UPDATED")),
            details_json=event_data.get("metadata") or {"description": event_data.get("description", "")},
        )
        
        db.add(activity_db)
        db.commit()
        db.refresh(activity_db)
        
        # Return Pydantic model for compatibility
        return ActivityEvent(
            event_id=activity_db.id,
            resource_type=ResourceType(activity_db.resource_type),
            resource_id=UUID(activity_db.resource_id) if activity_db.resource_id else uuid4(),
            event_type=activity_db.action,
            user_id=activity_db.user_id,
            description=activity_db.details_json.get("description", "") if activity_db.details_json else "",
            metadata=activity_db.details_json,
            timestamp=activity_db.created_at,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create activity event: {e}")
    finally:
        db.close()


def list_activity_events(
    tenant_id: UUID,
    resource_type: Optional[ResourceType] = None,
    resource_id: Optional[UUID] = None,
    limit: int = 100
) -> List[ActivityEvent]:
    """List activity events - from database"""
    return _list_activity_events(tenant_id, resource_type, resource_id, limit)


def _list_activity_events(
    tenant_id: UUID,
    resource_type: Optional[ResourceType] = None,
    resource_id: Optional[UUID] = None,
    limit: int = 100
) -> List[ActivityEvent]:
    """List activity events from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(ActivityEventDB).filter(ActivityEventDB.tenant_id == tenant_id)
        
        # Filter by resource_type if provided
        if resource_type:
            query = query.filter(ActivityEventDB.resource_type == resource_type.value)
        
        # Filter by resource_id if provided
        if resource_id:
            query = query.filter(ActivityEventDB.resource_id == str(resource_id))
        
        # Sort by created_at descending and limit
        events_db = query.order_by(desc(ActivityEventDB.created_at)).limit(limit).all()
        
        # Convert to Pydantic models for compatibility
        result = []
        for event_db in events_db:
            result.append(ActivityEvent(
                event_id=event_db.id,
                resource_type=ResourceType(event_db.resource_type),
                resource_id=UUID(event_db.resource_id) if event_db.resource_id else uuid4(),
                event_type=event_db.action,
                user_id=event_db.user_id,
                description=event_db.details_json.get("description", "") if event_db.details_json else "",
                metadata=event_db.details_json,
                timestamp=event_db.created_at,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_activity_events (DB): {e}")
        return []
    finally:
        db.close()
