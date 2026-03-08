"""Policy assumptions storage - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.policy import PolicyAssumption, Policy
from uepi_common.models_enhanced import PolicyAssumption as PydanticAssumption, ElasticityRange
from sqlalchemy import or_


def create_assumption(
    tenant_id: UUID,
    policy_id: UUID,
    assumption_data: Dict[str, Any]
) -> PydanticAssumption:
    """Create a new policy assumption - stored in database"""
    return _create_assumption(tenant_id, policy_id, assumption_data)


def _create_assumption(
    tenant_id: UUID,
    policy_id: UUID,
    assumption_data: Dict[str, Any]
) -> PydanticAssumption:
    """Create assumption in database"""
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
        
        # Create assumption in database
        assumption = PolicyAssumption(
            tenant_id=tenant_id,
            policy_id=policy_id_uuid,
            assumption_type=assumption_data.get("assumption_type", ""),
            description=assumption_data.get("description"),
            range_json=assumption_data.get("range") if isinstance(assumption_data.get("range"), dict) else None,
            value=str(assumption_data.get("value")) if assumption_data.get("value") is not None else None,
            source=assumption_data.get("source"),
            confidence=float(assumption_data.get("confidence", 0.5)) if assumption_data.get("confidence") else 0.5,
        )
        
        db.add(assumption)
        db.commit()
        db.refresh(assumption)
        
        # Return Pydantic model for compatibility
        return PydanticAssumption(
            assumption_type=assumption.assumption_type,
            description=assumption.description,
            range=assumption.range_json,
            value=assumption.value,
            source=assumption.source,
            confidence=assumption.confidence,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create assumption: {e}")
    finally:
        db.close()


def get_assumptions(
    tenant_id: UUID,
    policy_id: UUID | str
) -> List[Dict[str, Any]]:
    """Get all assumptions for a policy - from database"""
    return _get_assumptions(tenant_id, policy_id)


def _get_assumptions(
    tenant_id: UUID,
    policy_id: UUID | str
) -> List[Dict[str, Any]]:
    """Get assumptions from database"""
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
        
        # Query assumptions from database
        assumptions = db.query(PolicyAssumption).filter(
            PolicyAssumption.tenant_id == tenant_id,
            PolicyAssumption.policy_id == policy_id_uuid
        ).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for assumption in assumptions:
            assumption_dict = {
                "assumption_id": str(assumption.id),
                "assumption_type": assumption.assumption_type,
                "description": assumption.description,
                "range": assumption.range_json if assumption.range_json else None,
                "value": assumption.value,
                "source": assumption.source,
                "confidence": assumption.confidence if assumption.confidence else 0.5,
                "created_at": assumption.created_at.isoformat() if assumption.created_at else None,
                "updated_at": assumption.updated_at.isoformat() if assumption.updated_at else None,
            }
            result.append(assumption_dict)
        
        return result
        
    except Exception as e:
        print(f"ERROR get_assumptions (DB): {e}")
        return []
    finally:
        db.close()


def update_assumption(
    tenant_id: UUID,
    policy_id: UUID,
    assumption_id: str,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update a policy assumption - stored in database"""
    return _update_assumption(tenant_id, policy_id, assumption_id, updates)


def _update_assumption(
    tenant_id: UUID,
    policy_id: UUID,
    assumption_id: str,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update assumption in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        assumption_uuid = UUID(assumption_id)
        assumption = db.query(PolicyAssumption).filter(
            PolicyAssumption.id == assumption_uuid,
            PolicyAssumption.tenant_id == tenant_id,
            PolicyAssumption.policy_id == policy_id
        ).first()
        
        if not assumption:
            return None
        
        # Update fields
        if "assumption_type" in updates:
            assumption.assumption_type = updates["assumption_type"]
        if "description" in updates:
            assumption.description = updates["description"]
        if "value" in updates:
            assumption.value = str(updates["value"]) if updates["value"] is not None else None
        if "source" in updates:
            assumption.source = updates["source"]
        if "confidence" in updates:
            assumption.confidence = float(updates["confidence"]) if updates["confidence"] else 0.5
        if "range" in updates:
            assumption.range_json = updates["range"] if isinstance(updates["range"], dict) else None
        
        db.commit()
        db.refresh(assumption)
        
        # Return as dict (same format as file-based)
        return {
            "assumption_id": str(assumption.id),
            "assumption_type": assumption.assumption_type,
            "description": assumption.description,
            "range": assumption.range_json,
            "value": assumption.value,
            "source": assumption.source,
            "confidence": assumption.confidence,
            "created_at": assumption.created_at.isoformat() if assumption.created_at else None,
            "updated_at": assumption.updated_at.isoformat() if assumption.updated_at else None,
        }
        
    except ValueError:
        # assumption_id is not a valid UUID, return None
        return None
    except Exception as e:
        db.rollback()
        print(f"ERROR update_assumption (DB): {e}")
        return None
    finally:
        db.close()


def delete_assumption(
    tenant_id: UUID,
    policy_id: UUID,
    assumption_id: str
) -> bool:
    """Delete a policy assumption - stored in database"""
    return _delete_assumption(tenant_id, policy_id, assumption_id)


def _delete_assumption(
    tenant_id: UUID,
    policy_id: UUID,
    assumption_id: str
) -> bool:
    """Delete assumption from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        assumption_uuid = UUID(assumption_id)
        assumption = db.query(PolicyAssumption).filter(
            PolicyAssumption.id == assumption_uuid,
            PolicyAssumption.tenant_id == tenant_id,
            PolicyAssumption.policy_id == policy_id
        ).first()
        
        if not assumption:
            return False
        
        db.delete(assumption)
        db.commit()
        return True
        
    except ValueError:
        # assumption_id is not a valid UUID
        return False
    except Exception as e:
        db.rollback()
        print(f"ERROR delete_assumption (DB): {e}")
        return False
    finally:
        db.close()
