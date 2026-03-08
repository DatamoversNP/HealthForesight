"""File-based storage for notifications - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.notification import Notification as NotificationDB
from sqlalchemy import desc


def create_notification(
    tenant_id: UUID,
    notification_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new notification - stored in database"""
    return _create_notification(tenant_id, notification_data)


def _create_notification(
    tenant_id: UUID,
    notification_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create notification in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Map storage fields to database model
        notification_type = notification_data.get("type", notification_data.get("notification_type", "SYSTEM_ALERT"))
        category = notification_data.get("category", "SYSTEM")
        
        # Store action_url in metadata_json
        metadata_json = {}
        if notification_data.get("action_url"):
            metadata_json["action_url"] = notification_data["action_url"]
        if category:
            metadata_json["category"] = category
        
        notification_db = NotificationDB(
            tenant_id=tenant_id,
            user_id=UUID(notification_data["user_id"]) if notification_data.get("user_id") else None,
            notification_type=notification_type,
            title=notification_data.get("title", ""),
            message=notification_data.get("message", ""),
            metadata_json=metadata_json if metadata_json else None,
            read=False,
        )
        
        db.add(notification_db)
        db.commit()
        db.refresh(notification_db)
        
        # Return as dict (same format as file-based)
        return {
            "id": str(notification_db.id),
            "tenant_id": str(notification_db.tenant_id),
            "user_id": str(notification_db.user_id) if notification_db.user_id else None,
            "type": notification_db.notification_type,
            "category": notification_db.metadata_json.get("category", "SYSTEM") if notification_db.metadata_json else "SYSTEM",
            "title": notification_db.title,
            "message": notification_db.message,
            "action_url": notification_db.metadata_json.get("action_url") if notification_db.metadata_json else None,
            "read": notification_db.read,
            "created_at": notification_db.created_at.isoformat() if notification_db.created_at else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create notification: {e}")
    finally:
        db.close()


def list_notifications(
    tenant_id: UUID,
    user_id: Optional[UUID] = None,
    unread_only: bool = False,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List notifications for a tenant - from database"""
    return _list_notifications(tenant_id, user_id, unread_only, limit)


def _list_notifications(
    tenant_id: UUID,
    user_id: Optional[UUID] = None,
    unread_only: bool = False,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List notifications from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(NotificationDB).filter(NotificationDB.tenant_id == tenant_id)
        
        # Filter by user_id if provided
        if user_id:
            query = query.filter(NotificationDB.user_id == user_id)
        
        # Filter unread if requested
        if unread_only:
            query = query.filter(NotificationDB.read == False)
        
        # Sort by created_at descending and limit
        notifications_db = query.order_by(desc(NotificationDB.created_at)).limit(limit).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for notification_db in notifications_db:
            result.append({
                "id": str(notification_db.id),
                "tenant_id": str(notification_db.tenant_id),
                "user_id": str(notification_db.user_id) if notification_db.user_id else None,
                "type": notification_db.notification_type,
                "category": notification_db.metadata_json.get("category", "SYSTEM") if notification_db.metadata_json else "SYSTEM",
                "title": notification_db.title,
                "message": notification_db.message,
                "action_url": notification_db.metadata_json.get("action_url") if notification_db.metadata_json else None,
                "read": notification_db.read,
                "created_at": notification_db.created_at.isoformat() if notification_db.created_at else None,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_notifications (DB): {e}")
        return []
    finally:
        db.close()


def mark_notification_read(notification_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Mark a notification as read - from database"""
    return _mark_notification_read(notification_id, tenant_id)


def _mark_notification_read(notification_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Mark notification as read in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        notification_db = db.query(NotificationDB).filter(
            NotificationDB.id == notification_id,
            NotificationDB.tenant_id == tenant_id
        ).first()
        
        if not notification_db:
            return None
        
        notification_db.read = True
        notification_db.read_at = datetime.utcnow()
        
        db.commit()
        db.refresh(notification_db)
        
        # Return as dict (same format as file-based)
        return {
            "id": str(notification_db.id),
            "tenant_id": str(notification_db.tenant_id),
            "user_id": str(notification_db.user_id) if notification_db.user_id else None,
            "type": notification_db.notification_type,
            "category": notification_db.metadata_json.get("category", "SYSTEM") if notification_db.metadata_json else "SYSTEM",
            "title": notification_db.title,
            "message": notification_db.message,
            "action_url": notification_db.metadata_json.get("action_url") if notification_db.metadata_json else None,
            "read": notification_db.read,
            "read_at": notification_db.read_at.isoformat() if notification_db.read_at else None,
            "created_at": notification_db.created_at.isoformat() if notification_db.created_at else None,
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR mark_notification_read (DB): {e}")
        return None
    finally:
        db.close()


def mark_all_read(tenant_id: UUID, user_id: Optional[UUID] = None) -> int:
    """Mark all notifications as read - from database"""
    return _mark_all_read(tenant_id, user_id)


def _mark_all_read(tenant_id: UUID, user_id: Optional[UUID] = None) -> int:
    """Mark all notifications as read in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(NotificationDB).filter(
            NotificationDB.tenant_id == tenant_id,
            NotificationDB.read == False
        )
        
        # Filter by user_id if provided
        if user_id:
            query = query.filter(NotificationDB.user_id == user_id)
        
        notifications_db = query.all()
        
        # Update all to read
        count = 0
        for notification_db in notifications_db:
            notification_db.read = True
            notification_db.read_at = datetime.utcnow()
            count += 1
        
        db.commit()
        return count
        
    except Exception as e:
        db.rollback()
        print(f"ERROR mark_all_read (DB): {e}")
        return 0
    finally:
        db.close()


def get_unread_count(tenant_id: UUID, user_id: Optional[UUID] = None) -> int:
    """Get count of unread notifications - from database"""
    notifications = list_notifications(tenant_id, user_id=user_id, unread_only=True)
    return len(notifications)
