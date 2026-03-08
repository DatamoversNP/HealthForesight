"""Policy changelog storage - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.policy import PolicyChangelog, Policy
from uepi_common.models_enhanced import PolicyChangeLog
from sqlalchemy import or_, desc


def create_changelog_entry(
    tenant_id: UUID,
    policy_id: UUID,
    entry_data: Dict[str, Any]
) -> PolicyChangeLog:
    """Create a new changelog entry - stored in database"""
    return _create_changelog_entry(tenant_id, policy_id, entry_data)


def _create_changelog_entry(
    tenant_id: UUID,
    policy_id: UUID,
    entry_data: Dict[str, Any]
) -> PolicyChangeLog:
    """Create changelog entry in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Verify policy exists and convert policy_id if needed
        if isinstance(policy_id, str):
            policy = db.query(Policy).filter(
                Policy.tenant_id == tenant_id,
                or_(
                    Policy.id == policy_id,
                    Policy.policy_metadata_json['policy_id'].astext == policy_id
                )
            ).first()
            if not policy:
                raise ValueError(f"Policy {policy_id} not found")
            policy_id_uuid = policy.id
        else:
            policy_id_uuid = policy_id
            policy = db.query(Policy).filter(
                Policy.id == policy_id_uuid,
                Policy.tenant_id == tenant_id
            ).first()
            if not policy:
                raise ValueError(f"Policy {policy_id} not found")
        
        # Parse changed_by
        changed_by = None
        if entry_data.get("changed_by"):
            if isinstance(entry_data["changed_by"], str):
                changed_by = UUID(entry_data["changed_by"])
            else:
                changed_by = entry_data["changed_by"]
        
        # Parse changed_at
        changed_at = datetime.utcnow()
        if entry_data.get("changed_at"):
            if isinstance(entry_data["changed_at"], str):
                changed_at = datetime.fromisoformat(entry_data["changed_at"].replace("Z", "+00:00"))
            else:
                changed_at = entry_data["changed_at"]
        
        # Create changelog entry in database
        entry = PolicyChangelog(
            tenant_id=tenant_id,
            policy_id=policy_id_uuid,
            entry_type=entry_data.get("change_type", entry_data.get("entry_type", "UPDATED")),
            description=entry_data.get("reason") or entry_data.get("description"),
            changed_by=changed_by,
            changed_at=changed_at,
            changes_json={
                "field_name": entry_data.get("field_name"),
                "old_value": entry_data.get("old_value"),
                "new_value": entry_data.get("new_value"),
                "version_number": entry_data.get("version_number", 1),
            } if any(entry_data.get(k) for k in ["field_name", "old_value", "new_value", "version_number"]) else None,
        )
        
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        # Return Pydantic model for compatibility
        return PolicyChangeLog(
            change_id=entry.id,
            policy_id=entry.policy_id,
            version_number=entry.changes_json.get("version_number", 1) if entry.changes_json else 1,
            changed_by=entry.changed_by,
            changed_at=entry.changed_at,
            change_type=entry.entry_type,
            field_name=entry.changes_json.get("field_name") if entry.changes_json else None,
            old_value=entry.changes_json.get("old_value") if entry.changes_json else None,
            new_value=entry.changes_json.get("new_value") if entry.changes_json else None,
            reason=entry.description,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create changelog entry: {e}")
    finally:
        db.close()


def get_changelog(
    tenant_id: UUID,
    policy_id: UUID | str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get changelog entries for a policy - from database"""
    return _get_changelog(tenant_id, policy_id, limit)


def _get_changelog(
    tenant_id: UUID,
    policy_id: UUID | str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get changelog from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Convert policy_id to UUID if needed
        if isinstance(policy_id, str):
            try:
                policy_id_uuid = UUID(policy_id)
            except ValueError:
                # Not a UUID, find policy by string ID first
                policy = db.query(Policy).filter(
                    Policy.tenant_id == tenant_id,
                    or_(
                        Policy.id == policy_id,
                        Policy.policy_metadata_json['policy_id'].astext == policy_id
                    )
                ).first()
                if not policy:
                    return []
                policy_id_uuid = policy.id
        else:
            policy_id_uuid = policy_id
        
        # Query changelog entries from database (newest first)
        entries = db.query(PolicyChangelog).filter(
            PolicyChangelog.tenant_id == tenant_id,
            PolicyChangelog.policy_id == policy_id_uuid
        ).order_by(desc(PolicyChangelog.changed_at)).limit(limit).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for entry in entries:
            entry_dict = {
                "change_id": str(entry.id),
                "policy_id": str(entry.policy_id),
                "entry_type": entry.entry_type,
                "description": entry.description,
                "changed_by": str(entry.changed_by) if entry.changed_by else None,
                "changed_at": entry.changed_at.isoformat() if entry.changed_at else None,
                "changes_json": entry.changes_json,
            }
            # Extract fields from changes_json for compatibility
            if entry.changes_json:
                entry_dict["version_number"] = entry.changes_json.get("version_number", 1)
                entry_dict["field_name"] = entry.changes_json.get("field_name")
                entry_dict["old_value"] = entry.changes_json.get("old_value")
                entry_dict["new_value"] = entry.changes_json.get("new_value")
            entry_dict["change_type"] = entry.entry_type
            entry_dict["reason"] = entry.description
            result.append(entry_dict)
        
        return result
        
    except Exception as e:
        print(f"ERROR get_changelog (DB): {e}")
        return []
    finally:
        db.close()


def get_changelog_by_version(
    tenant_id: UUID,
    policy_id: UUID,
    version_number: int
) -> List[Dict[str, Any]]:
    """Get changelog entries for a specific version - from database"""
    all_entries = get_changelog(tenant_id, policy_id, limit=1000)
    return [e for e in all_entries if e.get("version_number") == version_number]


def get_changelog_by_type(
    tenant_id: UUID,
    policy_id: UUID,
    change_type: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get changelog entries filtered by change type - from database"""
    all_entries = get_changelog(tenant_id, policy_id, limit=1000)
    filtered = [e for e in all_entries if e.get("change_type") == change_type or e.get("entry_type") == change_type]
    return filtered[:limit]
