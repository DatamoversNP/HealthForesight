"""Policy version storage - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.policy import PolicyVersion as PolicyVersionDB, Policy
from uepi_common.models_enhanced import PolicyVersion, PolicyLifecycleState
from sqlalchemy import desc, or_


def create_policy_version(
    tenant_id: UUID,
    policy_id: UUID,
    version_data: Dict[str, Any]
) -> PolicyVersion:
    """Create a new policy version - stored in database"""
    return _create_policy_version(tenant_id, policy_id, version_data)


def _create_policy_version(
    tenant_id: UUID,
    policy_id: UUID,
    version_data: Dict[str, Any]
) -> PolicyVersion:
    """Create policy version in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Verify policy exists and get UUID if policy_id is string
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
        
        # Get current highest version number
        max_version = 0
        existing_versions = db.query(PolicyVersionDB).filter(
            PolicyVersionDB.tenant_id == tenant_id,
            PolicyVersionDB.policy_id == policy_id_uuid
        ).all()
        if existing_versions:
            max_version = max(v.version_number for v in existing_versions)
        
        version_number = max_version + 1
        
        # Parse dates
        effective_start_date = datetime.fromisoformat(version_data["effective_start_date"].replace("Z", "+00:00")) if isinstance(version_data.get("effective_start_date"), str) else version_data.get("effective_start_date", datetime.utcnow())
        effective_end_date = datetime.fromisoformat(version_data["effective_end_date"].replace("Z", "+00:00")) if version_data.get("effective_end_date") and isinstance(version_data["effective_end_date"], str) else version_data.get("effective_end_date")
        
        # Store metadata in version_metadata_json
        version_metadata = {
            "state": version_data.get("state", "DRAFT"),
            "change_summary": version_data.get("change_summary", ""),
            "change_details": version_data.get("change_details", {}),
            "created_by": str(version_data["created_by"]) if version_data.get("created_by") else None,
            "approved_by": str(version_data["approved_by"]) if version_data.get("approved_by") else None,
            "approved_at": version_data["approved_at"].isoformat() if version_data.get("approved_at") and hasattr(version_data.get("approved_at"), 'isoformat') else (version_data["approved_at"] if version_data.get("approved_at") else None),
        }
        
        # Create version in database
        version_db = PolicyVersionDB(
            tenant_id=tenant_id,
            policy_id=policy_id_uuid,
            version_number=version_number,
            effective_start_date=effective_start_date,
            effective_end_date=effective_end_date,
            change_type=version_data.get("change_type", "MINOR"),
            enforcement_strength=version_data.get("enforcement_strength", "STANDARD"),
            justification=version_data.get("change_summary") or version_data.get("justification"),
            version_metadata_json=version_metadata,
        )
        
        db.add(version_db)
        db.commit()
        db.refresh(version_db)
        
        # Return Pydantic model for compatibility
        return PolicyVersion(
            version_number=version_db.version_number,
            policy_id=version_db.policy_id,
            effective_start_date=version_db.effective_start_date,
            effective_end_date=version_db.effective_end_date,
            state=PolicyLifecycleState(version_metadata.get("state", "DRAFT")),
            change_summary=version_metadata.get("change_summary", ""),
            change_details=version_metadata.get("change_details", {}),
            created_by=UUID(version_metadata["created_by"]) if version_metadata.get("created_by") else None,
            created_at=version_db.created_at,
            approved_by=UUID(version_metadata["approved_by"]) if version_metadata.get("approved_by") else None,
            approved_at=datetime.fromisoformat(version_metadata["approved_at"]) if version_metadata.get("approved_at") and isinstance(version_metadata.get("approved_at"), str) else None,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create policy version: {e}")
    finally:
        db.close()


def get_policy_version(
    tenant_id: UUID,
    policy_id: UUID,
    version_number: int
) -> Optional[PolicyVersion]:
    """Get a specific policy version - from database"""
    return _get_policy_version(tenant_id, policy_id, version_number)


def _get_policy_version(
    tenant_id: UUID,
    policy_id: UUID,
    version_number: int
) -> Optional[PolicyVersion]:
    """Get policy version from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Convert policy_id to UUID if needed
        if isinstance(policy_id, str):
            policy = db.query(Policy).filter(
                Policy.tenant_id == tenant_id,
                or_(
                    Policy.id == policy_id,
                    Policy.policy_metadata_json['policy_id'].astext == policy_id
                )
            ).first()
            if not policy:
                return None
            policy_id_uuid = policy.id
        else:
            policy_id_uuid = policy_id
        
        version_db = db.query(PolicyVersionDB).filter(
            PolicyVersionDB.tenant_id == tenant_id,
            PolicyVersionDB.policy_id == policy_id_uuid,
            PolicyVersionDB.version_number == version_number
        ).first()
        
        if not version_db:
            return None
        
        # Return Pydantic model
        version_metadata = version_db.version_metadata_json if version_db.version_metadata_json else {}
        return PolicyVersion(
            version_number=version_db.version_number,
            policy_id=version_db.policy_id,
            effective_start_date=version_db.effective_start_date,
            effective_end_date=version_db.effective_end_date,
            state=PolicyLifecycleState(version_metadata.get("state", "DRAFT")),
            change_summary=version_metadata.get("change_summary", ""),
            change_details=version_metadata.get("change_details", {}),
            created_by=UUID(version_metadata["created_by"]) if version_metadata.get("created_by") else None,
            created_at=version_db.created_at,
            approved_by=UUID(version_metadata["approved_by"]) if version_metadata.get("approved_by") else None,
            approved_at=datetime.fromisoformat(version_metadata["approved_at"]) if version_metadata.get("approved_at") and isinstance(version_metadata.get("approved_at"), str) else None,
        )
        
    except Exception as e:
        print(f"ERROR get_policy_version (DB): {e}")
        return None
    finally:
        db.close()


def list_policy_versions(
    tenant_id: UUID,
    policy_id: UUID | str
) -> List[PolicyVersion]:
    """List all versions for a policy - from database"""
    return _list_policy_versions(tenant_id, policy_id)


def _list_policy_versions(
    tenant_id: UUID,
    policy_id: UUID | str
) -> List[PolicyVersion]:
    """List policy versions from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Convert policy_id to UUID if needed
        if isinstance(policy_id, str):
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
        
        # Query versions from database
        versions_db = db.query(PolicyVersionDB).filter(
            PolicyVersionDB.tenant_id == tenant_id,
            PolicyVersionDB.policy_id == policy_id_uuid
        ).order_by(desc(PolicyVersionDB.version_number)).all()
        
        # Convert to Pydantic models
        result = []
        for version_db in versions_db:
            version_metadata = version_db.version_metadata_json if version_db.version_metadata_json else {}
            result.append(PolicyVersion(
                version_number=version_db.version_number,
                policy_id=version_db.policy_id,
                effective_start_date=version_db.effective_start_date,
                effective_end_date=version_db.effective_end_date,
                state=PolicyLifecycleState(version_metadata.get("state", "DRAFT")),
                change_summary=version_metadata.get("change_summary", ""),
                change_details=version_metadata.get("change_details", {}),
                created_by=UUID(version_metadata["created_by"]) if version_metadata.get("created_by") else None,
                created_at=version_db.created_at,
                approved_by=UUID(version_metadata["approved_by"]) if version_metadata.get("approved_by") else None,
                approved_at=datetime.fromisoformat(version_metadata["approved_at"]) if version_metadata.get("approved_at") and isinstance(version_metadata.get("approved_at"), str) else None,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_policy_versions (DB): {e}")
        return []
    finally:
        db.close()


def get_latest_version(
    tenant_id: UUID,
    policy_id: UUID
) -> Optional[PolicyVersion]:
    """Get the latest version of a policy"""
    versions = list_policy_versions(tenant_id, policy_id)
    if not versions:
        return None
    return versions[0]  # Already sorted by version_number descending


def update_policy_version(
    tenant_id: UUID,
    policy_id: UUID,
    version_number: int,
    updates: Dict[str, Any]
) -> Optional[PolicyVersion]:
    """Update a policy version - stored in database"""
    return _update_policy_version(tenant_id, policy_id, version_number, updates)


def _update_policy_version(
    tenant_id: UUID,
    policy_id: UUID,
    version_number: int,
    updates: Dict[str, Any]
) -> Optional[PolicyVersion]:
    """Update policy version in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Convert policy_id to UUID if needed
        if isinstance(policy_id, str):
            policy = db.query(Policy).filter(
                Policy.tenant_id == tenant_id,
                or_(
                    Policy.id == policy_id,
                    Policy.policy_metadata_json['policy_id'].astext == policy_id
                )
            ).first()
            if not policy:
                return None
            policy_id_uuid = policy.id
        else:
            policy_id_uuid = policy_id
        
        version_db = db.query(PolicyVersionDB).filter(
            PolicyVersionDB.tenant_id == tenant_id,
            PolicyVersionDB.policy_id == policy_id_uuid,
            PolicyVersionDB.version_number == version_number
        ).first()
        
        if not version_db:
            return None
        
        # Update fields
        if "effective_start_date" in updates:
            version_db.effective_start_date = datetime.fromisoformat(updates["effective_start_date"].replace("Z", "+00:00")) if isinstance(updates["effective_start_date"], str) else updates["effective_start_date"]
        if "effective_end_date" in updates:
            version_db.effective_end_date = datetime.fromisoformat(updates["effective_end_date"].replace("Z", "+00:00")) if isinstance(updates["effective_end_date"], str) else (None if updates["effective_end_date"] is None else updates["effective_end_date"])
        if "change_type" in updates:
            version_db.change_type = updates["change_type"]
        if "enforcement_strength" in updates:
            version_db.enforcement_strength = updates["enforcement_strength"]
        if "justification" in updates or "change_summary" in updates:
            version_db.justification = updates.get("change_summary") or updates.get("justification", version_db.justification)
        
        # Update version_metadata_json
        version_metadata = version_db.version_metadata_json if version_db.version_metadata_json else {}
        if "state" in updates:
            version_metadata["state"] = updates["state"]
        if "change_summary" in updates:
            version_metadata["change_summary"] = updates["change_summary"]
        if "change_details" in updates:
            version_metadata["change_details"] = updates["change_details"]
        if "approved_by" in updates:
            version_metadata["approved_by"] = str(updates["approved_by"]) if updates["approved_by"] else None
        if "approved_at" in updates:
            version_metadata["approved_at"] = updates["approved_at"].isoformat() if updates["approved_at"] and hasattr(updates["approved_at"], 'isoformat') else updates["approved_at"]
        version_db.version_metadata_json = version_metadata
        
        # updated_at is automatically updated by SQLAlchemy
        
        db.commit()
        db.refresh(version_db)
        
        # Return Pydantic model for compatibility
        return PolicyVersion(
            version_number=version_db.version_number,
            policy_id=version_db.policy_id,
            effective_start_date=version_db.effective_start_date,
            effective_end_date=version_db.effective_end_date,
            state=PolicyLifecycleState(version_metadata.get("state", "DRAFT")),
            change_summary=version_metadata.get("change_summary", ""),
            change_details=version_metadata.get("change_details", {}),
            created_by=UUID(version_metadata["created_by"]) if version_metadata.get("created_by") else None,
            created_at=version_db.created_at,
            approved_by=UUID(version_metadata["approved_by"]) if version_metadata.get("approved_by") else None,
            approved_at=datetime.fromisoformat(version_metadata["approved_at"]) if version_metadata.get("approved_at") and isinstance(version_metadata.get("approved_at"), str) else None,
        )
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_policy_version (DB): {e}")
        return None
    finally:
        db.close()
